"""
Basic example of using structlog with Temporal.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    import structlog


structlog.configure(
    processors=[
        # Prepare event dict for `ProcessorFormatter`.
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
)

formatter = structlog.stdlib.ProcessorFormatter(
    processors=[structlog.dev.ConsoleRenderer()],
)

handler = logging.StreamHandler()
# Use OUR `ProcessorFormatter` to format all `logging` entries.
handler.setFormatter(formatter)
root_logger = logging.getLogger()
root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)


@activity.defn
def say_hello() -> None:
    """
    Basic activity that says hello to the world.
    """
    activity.logger.info("Hello World from Activity!")


# Basic workflow that logs and invokes an activity
@workflow.defn
class HelloWorldWorkflow:
    """
    Basic workflow that says hello to the world.
    """

    @workflow.run
    async def run(self) -> None:
        """
        Run the workflow.
        """
        workflow.logger.info("Hello World from Workflow!")
        return await workflow.execute_activity(
            say_hello,
            start_to_close_timeout=timedelta(seconds=10),
        )


async def main():
    client = await Client.connect("localhost:7233")
    logger = structlog.get_logger()
    logger.info("Temporal client connected.")

    async with Worker(
        client,
        task_queue="hello-activity-task-queue",
        workflows=[HelloWorldWorkflow],
        activities=[say_hello],
        activity_executor=ThreadPoolExecutor(5),
    ):

        result = await client.execute_workflow(
            HelloWorldWorkflow.run,
            id=f"structlog-hello-{uuid.uuid4()}",
            task_queue="hello-activity-task-queue",
        )
        logger.info(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
