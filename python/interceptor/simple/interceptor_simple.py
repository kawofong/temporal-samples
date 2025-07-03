"""
Simple Activity Interceptor.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, use `poe` to run the worker:

    ```bash
    uv run poe interceptor_simple
    ```
"""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

from python.interceptor.simple.interceptors import BasicCustomWorkerInterceptor

TASK_QUEUE = "interceptor-task-queue"


@activity.defn
def say_hello() -> None:
    """
    A basic activity that says hello.
    """
    activity.logger.info("Hello from Activity!")


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
            start_to_close_timeout=timedelta(seconds=2),
        )


async def main():
    """
    Main entry point.
    """
    import logging

    logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233")

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[HelloWorkflow],
        activities=[say_hello],
        activity_executor=ThreadPoolExecutor(5),
        interceptors=[BasicCustomWorkerInterceptor()],
    ):
        await client.execute_workflow(
            HelloWorkflow.run,
            id=f"hello-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


if __name__ == "__main__":
    asyncio.run(main())
