"""
Simple Worker Interceptor.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, use `poe` to run the worker:

    ```bash
    uv run poe interceptor_worker
    ```
"""

import asyncio
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

from python.interceptor.worker.interceptors import BasicCustomWorkerInterceptor

TASK_QUEUE = "interceptor-task-queue"


@activity.defn
def say_hello_for_a_long_time(
    greeting: str, iterations: int = 3, sleep: int = 1
) -> None:
    """
    A basic activity that says hello.
    """
    for i in range(iterations):
        activity.logger.info(f"{greeting} from Activity!")
        activity.heartbeat(i, sleep)
        time.sleep(sleep)


@workflow.defn
class HelloWorkflow:
    """
    A basic workflow that says hello.
    """

    def __init__(self):
        self._greeting = "Hello"

    @workflow.run
    async def run(self) -> None:
        """
        Workflow runner.
        """
        await workflow.execute_activity(
            say_hello_for_a_long_time,
            (self._greeting, 3),
            start_to_close_timeout=timedelta(seconds=10),
            heartbeat_timeout=timedelta(seconds=2),
            retry_policy=RetryPolicy(maximum_attempts=3),
        )

    @workflow.query
    def get_greeting(self) -> str:
        """
        Get the greeting.
        """
        return self._greeting

    @workflow.signal
    def set_greeting(self, greeting: str) -> None:
        """
        Set the greeting.
        """
        self._greeting = greeting

    @workflow.update
    def update_greeting(self, greeting: str) -> str:
        """
        Update the greeting.
        """
        self._greeting = greeting
        return self._greeting

    @update_greeting.validator
    def validate_greeting(self, greeting: str) -> None:
        """
        Validate the greeting.
        """
        if greeting == "":
            raise ValueError("Greeting cannot be empty")


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
        activities=[say_hello_for_a_long_time],
        activity_executor=ThreadPoolExecutor(5),
        interceptors=[BasicCustomWorkerInterceptor()],
    ):
        handle = await client.start_workflow(
            HelloWorkflow.run,
            id=f"hello-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )
        await handle.signal(HelloWorkflow.set_greeting, "Hola")
        greeting = await handle.execute_update(HelloWorkflow.update_greeting, "Hello")
        print(f"[Update] Greeting: {greeting}")
        await handle.result()
        greeting = await handle.query(HelloWorkflow.get_greeting)
        print(f"[Query] Greeting: {greeting}")


if __name__ == "__main__":
    asyncio.run(main())
