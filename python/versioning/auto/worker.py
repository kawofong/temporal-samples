import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor

from temporalio.client import Client
from temporalio.worker import Worker, WorkerDeploymentConfig, WorkerDeploymentVersion

from python.versioning.auto.activities import deposit, validate_transfer, withdraw
from python.versioning.auto.workflow import MoneyTransferWorkflow


async def main():
    """
    Main entry point.
    """
    logging.basicConfig(level=logging.INFO)

    client = await Client.connect("localhost:7233")

    worker = Worker(
        client,
        task_queue="versioning-basic-task-queue",
        workflows=[MoneyTransferWorkflow],
        activities=[deposit, validate_transfer, withdraw],
        activity_executor=ThreadPoolExecutor(2),
        deployment_config=WorkerDeploymentConfig(
            version=WorkerDeploymentVersion(
                deployment_name="money_transfer",
                build_id="V1",
            ),
            use_worker_versioning=True,
        ),
    )

    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
