"""
Workflow runner.
"""

import asyncio
import logging

from temporalio.worker import Worker

from common.python.client import TemporalClientFactory
from common.python.constants import ORDER_NOTIFICATION_TASK_QUEUE
from order_notification.activities.database import (
    get_order_details,
    get_user_preference,
    get_vendor_preference,
)
from order_notification.activities.notifications import (
    notify_user_push,
    notify_user_sms,
    notify_vendor_push,
    notify_vendor_sms,
)
from order_notification.workflows.orders import Orders


async def main():
    logging.basicConfig(level=logging.INFO)

    client = await TemporalClientFactory.create_client()

    worker = Worker(
        client,
        task_queue=ORDER_NOTIFICATION_TASK_QUEUE,
        workflows=[Orders],
        activities=[
            get_order_details,
            get_user_preference,
            get_vendor_preference,
            notify_user_push,
            notify_user_sms,
            notify_vendor_push,
            notify_vendor_sms,
        ],
    )
    print("\nWorker started, ctrl+c to exit\n")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
