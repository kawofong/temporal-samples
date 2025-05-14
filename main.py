"""
Workflow runner.
"""

import asyncio
import logging

from temporalio.client import Client
from temporalio.worker import Worker

from order_notification.workflows.orders import Orders


async def main():
    logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233", namespace="default")

    worker = Worker(
        client,
        task_queue="awefawef",
        workflows=[Orders],
        activities=[],
    )
    print("\nWorker started, ctrl+c to exit\n")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
