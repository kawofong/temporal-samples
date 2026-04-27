"""
Execute 3 ShipOrderActivities in parallel, each with a different order ID.

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

3. In another terminal, start the workflow:

    ```bash
    uv run poe parallel_activities
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
from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client

TASK_QUEUE = "ship-order-task-queue"


@dataclass
class ShipOrderInput:
    order_id: str
    customer_name: str
    destination: str
    fail_probs: float = field(default=0.0)


@activity.defn
def ship_order(input: ShipOrderInput) -> str:
    """
    Mock ShipOrderActivity - simulates shipping an order.

    Raises RuntimeError with probability `fail_probs` (0.0 = never, 1.0 = always).
    """
    activity.logger.info(
        "Shipping order %s for %s to %s (fail_probs=%.2f)",
        input.order_id,
        input.customer_name,
        input.destination,
        input.fail_probs,
    )
    if random.random() < input.fail_probs:
        raise RuntimeError(f"Failed to submit order {input.order_id}. Try again later.")
    return f"Order {input.order_id} shipped to {input.destination}"


@workflow.defn
class ShipOrderWorkflow:
    """
    Workflow that ships 3 orders in parallel.
    """

    @workflow.run
    async def run(self) -> list[str]:
        orders = [
            ShipOrderInput(
                order_id="ORD-001",
                customer_name="Alice",
                destination="New York, NY",
                fail_probs=0.0,
            ),
            ShipOrderInput(
                order_id="ORD-002",
                customer_name="Bob",
                destination="Los Angeles, CA",
                fail_probs=0.5,
            ),
            ShipOrderInput(
                order_id="ORD-003",
                customer_name="Carol",
                destination="Chicago, IL",
                fail_probs=0.7,
            ),
        ]

        results = await asyncio.gather(
            *[
                workflow.execute_activity(
                    ship_order,
                    order,
                    start_to_close_timeout=timedelta(seconds=30),
                )
                for order in orders
            ]
        )

        workflow.logger.info("All orders shipped: %s", results)
        return list(results)


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

    results = await client.execute_workflow(
        ShipOrderWorkflow.run,
        id=f"ship-order-workflow-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )

    for result in results:
        print(result)


if __name__ == "__main__":
    asyncio.run(main())
