import asyncio
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.common import RetryPolicy

from order_notification.schemas.notification import (
    NotificationChannelType,
    UserNotificationInput,
    UserNotificationMessageType,
    VendorNotificationInput,
    VendorNotificationMessageType,
)


# TODO(kawo): change activity argument to pydantic model
@activity.defn
async def notify_user_sms(
    arg: UserNotificationInput,
) -> None:
    """
    Send a SMS notification to an user about an order.
    """
    activity.logger.info(
        "Sending a SMS notification to user for order. order_id=%s. user_id=%s. message=%s",
        arg.order_id,
        arg.user_id,
        arg.message,
    )
    await asyncio.sleep(0.5)
    activity.logger.info(
        "SMS notification is sent to user for order. order_id=%s. user_id=%s. message=%s",
        arg.order_id,
        arg.user_id,
        arg.message,
    )


@activity.defn
async def notify_user_push(
    arg: UserNotificationInput,
) -> None:
    """
    Send a push notification to the user about an order.
    """
    activity.logger.info(
        "Sending a push notification to user for order. order_id=%s. user_id=%s. message=%s",
        arg.order_id,
        arg.user_id,
        arg.message,
    )
    await asyncio.sleep(0.5)
    activity.logger.info(
        "Push notification is sent to user for order. order_id=%s. user_id=%s. message=%s",
        arg.order_id,
        arg.user_id,
        arg.message,
    )


async def notify_user(
    arg: UserNotificationInput,
) -> None:
    """
    Send a notification to the user about an order based on their preference.
    """
    workflow.logger.info(
        "Notifying user. user_id=%s. preference=%s",
        arg.user_id,
        arg.user_notification_preference,
    )
    match arg.user_notification_preference:
        case NotificationChannelType.PUSH:
            await workflow.execute_activity(
                notify_user_push,
                arg,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
            )
        case NotificationChannelType.SMS:
            await workflow.execute_activity(
                notify_user_sms,
                arg,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
            )


@activity.defn
async def notify_vendor_sms(
    arg: VendorNotificationInput,
) -> None:
    """
    Send a SMS notification to the vendor about an order.
    """
    activity.logger.info(
        "Sending a SMS notification to vendor for order. order_id=%s. vendor_id=%s. message=%s",
        arg.order_id,
        arg.vendor_id,
        arg.message,
    )
    await asyncio.sleep(0.5)
    activity.logger.info(
        "SMS notification is sent to vendor for order. order_id=%s. vendor_id=%s. message=%s",
        arg.order_id,
        arg.vendor_id,
        arg.message,
    )


@activity.defn
async def notify_vendor_push(
    arg: VendorNotificationInput,
) -> None:
    """
    Send a push notification to the vendor about an order.
    """
    activity.logger.info(
        "Sending a push notification to vendor for order. order_id=%s. vendor_id=%s. message=%s",
        arg.order_id,
        arg.vendor_id,
        arg.message,
    )
    await asyncio.sleep(0.5)
    activity.logger.info(
        "Push notification is sent to vendor for order. order_id=%s. vendor_id=%s. message=%s",
        arg.order_id,
        arg.vendor_id,
        arg.message,
    )


async def notify_vendor(
    arg: VendorNotificationInput,
) -> None:
    """
    Send a notification to the vendor about an order based on their preference.
    """
    workflow.logger.info(
        "Notifying vendor. vendor_id=%s. preference=%s",
        arg.vendor_id,
        arg.vendor_notification_preference,
    )
    match arg.vendor_notification_preference:
        case NotificationChannelType.PUSH:
            await workflow.execute_activity(
                notify_vendor_push,
                arg,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
            )
        case NotificationChannelType.SMS:
            await workflow.execute_activity(
                notify_vendor_sms,
                arg,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
            )
