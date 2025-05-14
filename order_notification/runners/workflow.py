"""
Workflow runner.
"""

import asyncio
import uuid

from common.python.client import TemporalClientFactory
from common.python.constants import ORDER_NOTIFICATION_TASK_QUEUE
from order_notification.schemas.order import OrderWorkflowInput
from order_notification.workflows.orders import Orders


async def main():
    client = await TemporalClientFactory.create_client()

    # Execute a workflow
    dummy_order_id = "dummy-order-id"
    print(f"Placing an order. order_id={dummy_order_id}")
    result = await client.execute_workflow(
        Orders.run,
        OrderWorkflowInput(order_id=dummy_order_id, expiration_time=30),
        id=dummy_order_id,
        task_queue=ORDER_NOTIFICATION_TASK_QUEUE,
    )

    print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
