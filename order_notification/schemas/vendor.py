"""
Schema for order notification workflow.
"""

from pydantic import BaseModel

from order_notification.schemas.notification import NotificationChannelType


class VendorPreference(BaseModel):
    """
    Vendor notification preferences.
    """

    vendor_id: str
    notification_preference: NotificationChannelType = NotificationChannelType.PUSH
