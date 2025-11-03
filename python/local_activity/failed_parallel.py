"""
Demonstrate behavior of parallel local activities that fail.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, use `poe` to run the workflow:

    ```bash
    uv run poe failed_parallel
    ```
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig
from temporalio.worker import Worker

TASK_QUEUE = "failed-parallel-task-queue"


@activity.defn
def success() -> None:
    """
    A basic activity that succeeds.
    """
    activity.logger.info("Success from Activity!")


@activity.defn
def fail() -> None:
    """
    A basic activity that fails.
    """
    raise RuntimeError("Failed to say hello.")


@workflow.defn
class HelloWorkflow:
    """
    A basic workflow that says hello.
    """

    @workflow.run
    async def run(self) -> None:
        """
        Workflow runner.
        """
        # Create a list of tasks: 10 success activities and 1 fail activity
        tasks = []

        # Add 10 success activities
        for i in range(10):
            task = workflow.start_local_activity(
                success,
                start_to_close_timeout=timedelta(seconds=1),
            )
            tasks.append(task)

        # Add 1 fail activity
        fail_task = workflow.start_local_activity(
            fail,
            start_to_close_timeout=timedelta(seconds=1),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2,
                maximum_interval=timedelta(seconds=20),
            ),
        )
        tasks.append(fail_task)

        # Wait for all activities to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            workflow.logger.info(f"Some activities failed: {e}")

        workflow.logger.info("All activities completed")


async def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)

    client = await Client.connect(
        "localhost:7233",
        runtime=Runtime(
            telemetry=TelemetryConfig(
                metrics=PrometheusConfig(bind_address="0.0.0.0:9000")
            )
        ),
    )

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[HelloWorkflow],
        activities=[success, fail],
        activity_executor=ThreadPoolExecutor(5),
    ):
        await client.execute_workflow(
            HelloWorkflow.run,
            id=f"hello-workflow-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


if __name__ == "__main__":
    asyncio.run(main())
