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
    await handle.signal(Orders.accept_order)
    # await handle.signal(Orders.prepare_order)
    # await handle.signal(Orders.ready_order)
    # await handle.signal(Orders.pick_up_order)
    # await handle.signal(Orders.decline_order)


if __name__ == "__main__":
    asyncio.run(main())
