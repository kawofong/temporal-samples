from enum import StrEnum

from pydantic import BaseModel


class NotificationChannelType(StrEnum):
    SMS = "SMS"
    PUSH = "PUSH"


class VendorNotificationMessageType(StrEnum):
    NEW_ORDER = "NEW_ORDER"


class UserNotificationMessageType(StrEnum):
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_CANCELED = "ORDER_CANCELED"
    ORDER_BEING_PREPARED = "ORDER_BEING_PREPARED"
    ORDER_READY = "ORDER_READY"
    ORDER_COMPLETED = "ORDER_COMPLETED"


class UserNotificationInput(BaseModel):
    order_id: str
    user_id: str
    message: UserNotificationMessageType
    user_notification_preference: NotificationChannelType | None = None


class VendorNotificationInput(BaseModel):
    order_id: str
    vendor_id: str
    message: VendorNotificationMessageType
    vendor_notification_preference: NotificationChannelType | None = None
