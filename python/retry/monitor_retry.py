"""
Monitor high number of retries.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, use `poe` to run the workflow:

    ```bash
    uv run poe monitor_retry
    ```

3. Navigate to http://localhost:9000/metrics to see the metrics.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ApplicationError
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig
from temporalio.worker import Worker

TASK_QUEUE = "monitor-retry-task-queue"


@activity.defn
def say_hello() -> None:
    """
    A basic activity that says hello.
    """
    activity.logger.info("Hello from Activity!")
    attempt = activity.info().attempt

    try:
        # Always raise an error to test the retry logic.
        raise RuntimeError("Failed to say hello.")
    except RuntimeError as e:
        activity_meter = activity.metric_meter()
        high_retry_counter = activity_meter.create_counter(
            name="custom_high_retry_counter",
            description="A counter for the number of high retry attempts.",
            unit="count",
        )
        if attempt > 10:
            activity.logger.info("High retry attempt %s", attempt)
            high_retry_counter.add(1)
        if attempt > 20:
            activity.logger.info("Delay next retry. %s", attempt)
            raise ApplicationError(
                f"Delay next retry. {attempt}",
                next_retry_delay=timedelta(seconds=2),
            ) from e
        raise e


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
        await workflow.execute_activity(
            say_hello,
            start_to_close_timeout=timedelta(seconds=1),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=0.5),
                backoff_coefficient=2,
                maximum_interval=timedelta(seconds=1),
                maximum_attempts=100,
            ),
        )


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
        activities=[say_hello],
        activity_executor=ThreadPoolExecutor(5),
    ):
        await client.execute_workflow(
            HelloWorkflow.run,
            id=f"hello-workflow-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


if __name__ == "__main__":
    asyncio.run(main())
