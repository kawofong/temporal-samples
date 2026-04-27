"""
Worker for the `python/schedule` samples.

Runs a single worker on task queue "ship-order-task-queue" that serves both:
  - ShipOrderWorkflow          (parallel activities demo)
  - ResumableShipOrderWorkflow (resumable activities demo)

Supports local dev server and Temporal Cloud via environment variables:

    TEMPORAL_ADDRESS    Server address (default: localhost:7233)
    TEMPORAL_NAMESPACE  Namespace (default: default)
    TEMPORAL_API_KEY    API key - when set, enables TLS and targets Temporal Cloud

To start the worker against the local dev server:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, start this worker:

    ```bash
    uv run poe schedule_worker
    ```
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker

from python.schedule.parallel_activities import (
    TASK_QUEUE,
    ShipOrderWorkflow,
    ship_order,
)
from python.schedule.resumable_activities import (
    ResumableShipOrderWorkflow,
    resumable_ship_order,
)


async def connect_client() -> Client:
    """
    Connect to Temporal using environment variables.

    When TEMPORAL_API_KEY is set the client connects to Temporal Cloud with TLS
    and API-key authentication. Otherwise it connects to the local dev server.
    """
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    api_key = os.environ.get("TEMPORAL_API_KEY")

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


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    client = await connect_client()

    logger.info("Starting worker on task queue '%s'", TASK_QUEUE)

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ShipOrderWorkflow, ResumableShipOrderWorkflow],
        activities=[ship_order, resumable_ship_order],
        activity_executor=ThreadPoolExecutor(10),
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
