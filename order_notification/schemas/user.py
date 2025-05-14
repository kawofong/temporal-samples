"""
Schema for order notification workflow.
"""

from pydantic import BaseModel

from order_notification.schemas.notification import NotificationChannelType


class UserPreference(BaseModel):
    """
    User notification preferences.
    """

    user_id: str
    notification_preference: NotificationChannelType = NotificationChannelType.PUSH
