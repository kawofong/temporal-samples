"""
Signal runner.
"""

import asyncio

from common.python.client import TemporalClientFactory
from order_notification.workflows.orders import Orders


async def main():
    client = await TemporalClientFactory.create_client()

    handle = client.get_workflow_handle_for(
        Orders.run,
        "dummy-order-id",
    )
    result = await handle.query(Orders.query_order_state)
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
