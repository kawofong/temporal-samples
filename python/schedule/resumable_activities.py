"""
Execute 3 ShipOrderActivities in parallel.
Pauses the Workflow when any activity fails 5 times consecutively and waits
for a per-order `continue` signal before retrying.

Requires the schedule worker to be running (`uv run poe schedule_worker`).

Supports running against the local Temporal dev server or Temporal Cloud, controlled
entirely through environment variables:

    TEMPORAL_ADDRESS    Server address (default: localhost:7233)
    TEMPORAL_NAMESPACE  Namespace (default: default)
    TEMPORAL_API_KEY    API key - when set, enables TLS and targets Temporal Cloud

To run against the local dev server:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, start the worker:

    ```bash
    uv run poe schedule_worker
    ```

3. In another terminal, start the workflow (prints the workflow ID):

    ```bash
    uv run poe resumable_activities
    ```

4. To unblock a paused order, send the `continue` signal with the order ID:

    ```bash
    temporal workflow signal \\
        --workflow-id <workflow-id> \\
        --name continue_signal \\
        --input '"<order-id>"'
    ```

To run against Temporal Cloud, export the environment variables first:

    ```bash
    export TEMPORAL_ADDRESS="<namespace>.<accountId>.tmprl.cloud:7233"
    export TEMPORAL_NAMESPACE="<namespace>.<accountId>"
    export TEMPORAL_API_KEY="<your-api-key>"
    ```
"""

import asyncio
import logging
import os
import random
import uuid
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, ApplicationError

from python.schedule.parallel_activities import TASK_QUEUE, ShipOrderInput


class DownStreamError(ApplicationError):
    """
    Error indicating a down stream error requiring human intervention.
    """


@activity.defn
def resumable_ship_order(input: ShipOrderInput) -> str:
    """
    Mock ShipOrderActivity for the resumable workflow.

    Raises DownStreamError (non-retryable) after 5 attempts, signalling that
    human intervention is required. Also fails randomly based on `fail_probs`.
    """
    retry_count = activity.info().attempt
    activity.logger.info(
        "Shipping order %s for %s to %s (retry_count=%d)",
        input.order_id,
        input.customer_name,
        input.destination,
        retry_count,
    )
    if retry_count > 5:
        raise DownStreamError(
            "Detecting down stream error, requiring human intervention.",
            non_retryable=True,
            type="DownStreamError",
        )
    if random.random() < input.fail_probs:
        raise RuntimeError(f"Failed to submit order {input.order_id}. Try again later.")
    return f"Order {input.order_id} shipped to {input.destination}"


@workflow.defn
class ResumableShipOrderWorkflow:
    """
    Workflow that ships 3 orders in parallel.

    Any order that fails 5 times in a row causes the
    workflow to pause. It resumes only after a `continue` signal is received, at
    which point all paused orders reset their failure counters and retry.
    """

    def __init__(self) -> None:
        self._pause_tracker = {}

    @workflow.signal
    async def continue_signal(self, order_id: str) -> None:
        """Resume all paused activities and reset their failure counters."""
        workflow.logger.info(
            "Received 'continue' signal for order %s",
            order_id,
        )
        self._pause_tracker[order_id] = False

    @workflow.run
    async def run(self) -> list[str]:
        orders = [
            ShipOrderInput(
                order_id="ord-001",
                customer_name="Alice",
                destination="New York, NY",
                fail_probs=0.0,
            ),
            ShipOrderInput(
                order_id="ord-002",
                customer_name="Bob",
                destination="Los Angeles, CA",
                fail_probs=0.8,
            ),
            ShipOrderInput(
                order_id="ord-003",
                customer_name="Carol",
                destination="Chicago, IL",
                fail_probs=0.99,
            ),
        ]
        self._pause_tracker = {order.order_id: False for order in orders}

        results = await asyncio.gather(
            *[self._resumable_activity(order) for order in orders]
        )

        workflow.logger.info("All orders shipped: %s", results)
        return list(results)

    async def _resumable_activity(self, order: ShipOrderInput) -> str:
        """
        Make a resumable activity call.
        """
        self._pause_tracker[order.order_id] = False
        result = None
        while result is None:
            try:
                result = await workflow.execute_activity(
                    resumable_ship_order,
                    order,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=RetryPolicy(
                        maximum_interval=timedelta(seconds=1),
                    ),
                )
            except ActivityError as e:
                if (
                    isinstance(e.cause, ApplicationError)
                    and e.cause.type == "DownStreamError"
                ):
                    workflow.logger.info(
                        "Pausing workflow, requires human intervention."
                    )
                    self._pause_tracker[order.order_id] = True
                    await workflow.wait_condition(
                        lambda: not self._pause_tracker[order.order_id]
                    )
                    workflow.logger.info("Resuming activity after human intervention.")

        return result


async def connect_client() -> Client:
    """
    Connect to Temporal using environment variables.

    When TEMPORAL_API_KEY is set the client connects to Temporal Cloud with TLS
    and API-key authentication. Otherwise it connects to the local dev server.
    """
    address = str(os.environ.get("TEMPORAL_ADDRESS", "localhost:7233"))
    namespace = str(os.environ.get("TEMPORAL_NAMESPACE", "default"))
    api_key = str(os.environ.get("TEMPORAL_API_KEY"))

    if api_key:
        logging.getLogger(__name__).info(
            "Connecting to Temporal Cloud at %s (namespace=%s)", address, namespace
        )
        return await Client.connect(
            address,
            namespace=namespace,
            api_key=api_key,
            tls=True,
        )

    logging.getLogger(__name__).info(
        "Connecting to local dev server at %s (namespace=%s)", address, namespace
    )
    return await Client.connect(address, namespace=namespace)


async def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)

    client = await connect_client()

    workflow_id = f"resumable-ship-order-workflow-{uuid.uuid4()}"
    handle = await client.start_workflow(
        ResumableShipOrderWorkflow.run,
        id=workflow_id,
        task_queue=TASK_QUEUE,
    )

    print(f"Started workflow: {handle.id}")
    print(
        f"To resume a paused order, run:\n"
        f"  temporal workflow signal \\\n"
        f"      --workflow-id {handle.id} \\\n"
        f"      --name continue_signal \\\n"
        f'      --input \'"<order-id>"\''
    )


if __name__ == "__main__":
    asyncio.run(main())
