"""
Worker for the expirable payment workflow.
"""

import asyncio
import logging

from temporalio.worker import Worker

from common.python.client import TemporalClientFactory
from python.expirable_workflow.activities import (
    accept_payment,
    check_fraud,
    notify_customer,
    validate_payment,
)
from python.expirable_workflow.workflow import ExpirablePaymentWorkflow

TASK_QUEUE = "expirable-payment-queue"


async def main():
    logging.basicConfig(level=logging.INFO)

    client = await TemporalClientFactory.create_client()

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[ExpirablePaymentWorkflow],
        activities=[
            validate_payment,
            check_fraud,
            accept_payment,
            notify_customer,
        ],
    )
    print("\nExpirable Payment Worker started, ctrl+c to exit\n")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
