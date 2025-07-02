"""
Temporal Worker for the Observability Workflow.
"""

import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.runtime import PrometheusConfig, Runtime, TelemetryConfig
from temporalio.worker import Worker

from python.observability.custom_metrics import (
    TASK_QUEUE,
    BatchHelloWorkflow,
    HelloWorkflow,
    say_hello,
)

logging.basicConfig(level=logging.INFO)

# Create a new runtime that has telemetry enabled. Create this first to avoid
# the default Runtime from being lazily created.
observable_runtime = Runtime(
    telemetry=TelemetryConfig(metrics=PrometheusConfig(bind_address="0.0.0.0:9000"))
)


async def main():
    """
    Main function.
    """
    # Start client
    client = await Client.connect(
        "localhost:7233",
        runtime=observable_runtime,
    )

    # Run a worker for the workflow
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[BatchHelloWorkflow, HelloWorkflow],
        activities=[say_hello],
        activity_executor=ThreadPoolExecutor(max_workers=10),
    )
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
