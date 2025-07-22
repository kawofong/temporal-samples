"""
A basic workflow to demonstrate Worker Versioning.

Reference: https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev \
        --search-attribute Step=Keyword \
        --dynamic-config-value frontend.workerVersioningWorkflowAPIs=true \
        --dynamic-config-value system.enableDeploymentVersions=true
    ```

1. In a new terminal, use `poe` to run the Worker:

    ```bash
    uv run poe versioning_basic_worker
    ```

1. Use the `temporal` CLI to describe the Worker Deployment:

    ```bash
    temporal worker deployment describe --name="money_transfer"
    ```

1. In a new terminal, use `poe` to run the V1 Workflow:

    ```bash
    uv run poe versioning_basic_workflow
    ```

1. Use the `temporal` CLI to activate the Worker Deployment Version:

    ```bash
    temporal worker deployment set-current-version \
        --deployment-name "money_transfer" \
        --build-id "V1"
    ```

1. In a new terminal, use `poe` to run the Worker:

    ```bash
    uv run poe versioning_basic_worker_v2
    ```

1. Use the `temporal` CLI to ramp up traffic to Deployment V2:

    ```bash
    temporal worker deployment set-ramping-version \
        --deployment-name "money_transfer" \
        --build-id "V2" \
        --percentage=50
    ```

1. Use the `temporal` CLI to rollback to V1:

    ```bash
    temporal worker deployment set-ramping-version \
        --deployment-name "money_transfer" \
        --build-id "V2" \
        --percentage=0
    ```

1. Use the `temporal` CLI to fully ramp traffic to V2:

    ```bash
    temporal worker deployment set-current-version \
        --deployment-name "money_transfer" \
        --build-id "V2"
    ```

1. After the Deployment Version V1 is drained, use the `temporal` CLI to sunset V1:

    ```bash
    temporal worker deployment delete-version \
        --deployment-name "money_transfer" \
        --build-id "V1"
    ```
"""

import asyncio
import uuid
from datetime import timedelta

from temporalio import workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy, SearchAttributeKey, VersioningBehavior

with workflow.unsafe.imports_passed_through():
    from python.versioning.basic.activities import deposit, validate_transfer, withdraw


@workflow.defn(
    name="MoneyTransferWorkflow", versioning_behavior=VersioningBehavior.PINNED
)
class MoneyTransferWorkflow:
    """
    A basic workflow that transfers money between two accounts.
    """

    WORKFLOW_STEP = SearchAttributeKey.for_keyword("Step")

    @workflow.run
    async def run(self) -> None:
        """
        Workflow runner.
        """
        workflow_id = workflow.info().workflow_id
        workflow.logger.info(f"Workflow ID: {workflow_id}")

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("VALIDATING")])
        await workflow.execute_activity(
            validate_transfer,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("WITHDRAWING")])
        await workflow.execute_activity(
            withdraw,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("DEPOSITING")])
        await workflow.execute_activity(
            deposit,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )


async def main():
    """
    Main entry point.
    """
    client = await Client.connect("localhost:7233")

    for _ in range(100):
        await client.execute_workflow(
            MoneyTransferWorkflow.run,
            id=f"money-transfer-workflow-{uuid.uuid4()}",
            task_queue="versioning-basic-task-queue",
        )
        await asyncio.sleep(1.0)


if __name__ == "__main__":
    asyncio.run(main())
