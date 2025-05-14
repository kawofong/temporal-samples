import random
import uuid
from datetime import datetime

import pytz
from temporalio import activity

from order_notification.schemas.notification import NotificationChannelType
from order_notification.schemas.order import OrderDetails
from order_notification.schemas.user import UserPreference
from order_notification.schemas.vendor import VendorPreference


@activity.defn
async def get_order_details(order_id: str) -> OrderDetails:
    """
    Get order details from the database.
    """
    activity.logger.info(
        "Retrieving order details from database. order_id=%s", order_id
    )
    order_details = OrderDetails(
        order_id=order_id,
        user_id=str(uuid.uuid4()),
        vendor_id=str(uuid.uuid4()),
        order_date=datetime.now(tz=pytz.UTC),
    )
    return order_details


@activity.defn
async def get_user_preference(user_id: str) -> UserPreference:
    """
    Get user preferences from the database.
    """
    activity.logger.info(
        "Retrieving user preferences from database. user_id=%s", user_id
    )
    return UserPreference(
        user_id=user_id,
        notification_preference=random.choice(list(NotificationChannelType)),
    )


@activity.defn
async def get_vendor_preference(vendor_id: str) -> VendorPreference:
    """
    Get vendor preferences from the database.
    """
    activity.logger.info(
        "Retrieving vendor preferences from database. vendor_id=%s", vendor_id
    )
    return VendorPreference(
        vendor_id=vendor_id,
        notification_preference=random.choice(list(NotificationChannelType)),
    )
