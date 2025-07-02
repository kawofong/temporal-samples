"""
Custom metrics to observe Temporal Workflows.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, use `poe` to run the worker:

    ```bash
    uv run poe observability_worker
    ```

3. In a new terminal, use `poe` to run a workflow:

    ```bash
    uv run poe custom_metrics
    ```

4. Navigate to http://localhost:9000/metrics to see the metrics.

5. Confirm that the custom metrics (`custom_batch_hello_success` and `custom_batch_hello_failure`) are being reported.
    * Try running this workflow multiple times to generate more cardinality for the metrics.
"""

import asyncio
import random
import uuid
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError
from temporalio.workflow import ParentClosePolicy

TASK_QUEUE = "observability-task-queue"


@workflow.defn
class BatchHelloWorkflow:
    """
    A batch Workflow that runs hello world workflows.
    """

    @workflow.run
    async def run(self, iterations: int = 10) -> None:
        """
        Workflow runner.
        """
        tasks = []
        batch_id = workflow.info().workflow_id
        workflow.logger.info("Starting batch hello. batch_id=%s.", batch_id)
        for i in range(iterations):
            task = workflow.start_child_workflow(
                HelloWorkflow.run,
                HelloWorkflowInput(batch_id=batch_id, hello_id=f"{i}"),
                id=f"{batch_id}-hello-{i}",
                task_queue=TASK_QUEUE,
                parent_close_policy=ParentClosePolicy.ABANDON,
            )
            tasks.append(task)
        results = await asyncio.gather(*tasks)
        workflow.logger.info("All workflows completed. iter=%s", iterations)
        workflow.logger.info("Results: %s", results)


@dataclass
class SayHelloActivityInput:
    """
    Input for the HelloWorkflow.
    """

    batch_id: str
    hello_id: str


@activity.defn
def say_hello(arg: SayHelloActivityInput) -> None:
    """
    A basic activity that says hello.
    """
    # With a certain probability, raise an exception
    if random.random() <= 0.8:
        raise RuntimeError("Failed to say hello.")
    activity.logger.info(
        "Hello from Activity! batch_id=%s, hello_id=%s",
        arg.batch_id,
        arg.hello_id,
    )


@dataclass
class HelloWorkflowInput:
    """
    Input for the HelloWorkflow.
    """

    batch_id: str
    hello_id: str


@workflow.defn
class HelloWorkflow:
    """
    A basic workflow that says hello.
    """

    def __init__(self):
        self._workflow_meter = workflow.metric_meter()
        self._success_counter = self._workflow_meter.create_counter(
            name="custom_batch_hello_success",
            description="A counter for the number of successful hello calls in a batch.",
            unit="count",
        )
        self._failure_counter = self._workflow_meter.create_counter(
            name="custom_batch_hello_failure",
            description="A counter for the number of failed hello calls in a batch.",
            unit="count",
        )

    @workflow.run
    async def run(self, arg: HelloWorkflowInput) -> None:
        """
        Workflow runner.
        """
        try:
            await workflow.execute_activity(
                say_hello,
                SayHelloActivityInput(batch_id=arg.batch_id, hello_id=arg.hello_id),
                start_to_close_timeout=timedelta(seconds=2),
                retry_policy=RetryPolicy(
                    maximum_attempts=2,
                ),
            )
        except ActivityError as e:
            # Increment the failure counter
            self._failure_counter.add(
                1,
                additional_attributes={"batch_id": arg.batch_id},
            )
            raise e

        # Increment the success counter
        self._success_counter.add(
            1,
            additional_attributes={"batch_id": arg.batch_id},
        )


async def main():
    """
    Main entry point.
    """
    client = await Client.connect("localhost:7233")

    await client.execute_workflow(
        BatchHelloWorkflow.run,
        10,
        id=f"batch-hello-{uuid.uuid4()}",
        task_queue=TASK_QUEUE,
    )


if __name__ == "__main__":
    asyncio.run(main())
