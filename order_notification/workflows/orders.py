"""
Order notification workflow.
"""

import asyncio
from datetime import datetime, timedelta
from typing import Callable

from temporalio import workflow
from temporalio.common import RetryPolicy

from order_notification.schemas.notification import (
    UserNotificationInput,
    VendorNotificationInput,
)

# Import activity, passing it through the sandbox without reloading the module
with workflow.unsafe.imports_passed_through():
    from order_notification.activities.database import (
        get_order_details,
        get_user_preference,
        get_vendor_preference,
    )
    from order_notification.activities.notifications import notify_user, notify_vendor
    from order_notification.schemas.notification import (
        UserNotificationMessageType,
        VendorNotificationMessageType,
    )
    from order_notification.schemas.order import (
        OrderDetails,
        OrderState,
        OrderWorkflowInput,
    )
    from order_notification.schemas.user import UserPreference
    from order_notification.schemas.vendor import VendorPreference


@workflow.defn
class Orders:
    """
    Workflow to manage orders for users.
    """

    @workflow.init
    def __init__(self, arg: OrderWorkflowInput) -> None:
        self.order_state: OrderState = OrderState.ORDER_PLACED
        self.order_start_time: datetime = workflow.now()
        self.is_new_state: bool = False
        self.order_expiration_time: timedelta = timedelta(seconds=arg.expiration_time)

    @workflow.run
    async def run(self, arg: OrderWorkflowInput) -> OrderState:
        """
        Workflow logic.
        """
        workflow.logger.info("Placing an order. order_id=%s", arg.order_id)

        # 1. Retrieve order details from database
        order_details: OrderDetails = await workflow.execute_activity(
            get_order_details,
            arg.order_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
        )

        # 2. Retrieve vendor notification preference from database
        vendor_preference: VendorPreference = await workflow.execute_activity(
            get_vendor_preference,
            arg.order_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
        )

        # 3. Sends notification to vendor based on their preferences
        await notify_vendor(
            VendorNotificationInput(
                order_id=arg.order_id,
                vendor_id=order_details.vendor_id,
                vendor_notification_preference=vendor_preference.notification_preference,
                message=VendorNotificationMessageType.NEW_ORDER,
            )
        )

        self.order_state = OrderState.VENDOR_NOTIFIED
        workflow.logger.info(
            "Vendor notified. order_id=%s. vendor_id=%s",
            arg.order_id,
            order_details.vendor_id,
        )

        # 4. Retrieve user notification preference from database
        user_preference: UserPreference = await workflow.execute_activity(
            get_user_preference,
            arg.order_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(maximum_interval=timedelta(seconds=5)),
        )

        remaining_expiration_time = self.order_expiration_time
        while True:
            # 5. Wait for order state transitions
            remaining_expiration_time = await self._wait_with_expiration(
                lambda: self.is_new_state,
                expiration_time=remaining_expiration_time,
            )
            workflow.logger.warning(
                "Remaining expiration time: %s", remaining_expiration_time
            )

            match self.order_state:
                case OrderState.ORDER_ACCEPTED:
                    # If the order is accepted, then notify the user
                    workflow.logger.info(
                        "Order accepted. order_id=%s. vendor_id=%s",
                        arg.order_id,
                        order_details.vendor_id,
                    )
                    await notify_user(
                        UserNotificationInput(
                            order_id=arg.order_id,
                            user_id=order_details.user_id,
                            user_notification_preference=user_preference.notification_preference,
                            message=UserNotificationMessageType.ORDER_ACCEPTED,
                        )
                    )
                case OrderState.ORDER_PREPARATION:
                    # If the order is being prepared, then notify the user
                    workflow.logger.info(
                        "Order is being prepared. order_id=%s. vendor_id=%s",
                        arg.order_id,
                        order_details.vendor_id,
                    )
                    await notify_user(
                        UserNotificationInput(
                            order_id=arg.order_id,
                            user_id=order_details.user_id,
                            user_notification_preference=user_preference.notification_preference,
                            message=UserNotificationMessageType.ORDER_BEING_PREPARED,
                        )
                    )
                case OrderState.ORDER_READY:
                    # If the order is ready, then notify the user
                    workflow.logger.info(
                        "Order is ready. order_id=%s. vendor_id=%s",
                        arg.order_id,
                        order_details.vendor_id,
                    )
                    await notify_user(
                        UserNotificationInput(
                            order_id=arg.order_id,
                            user_id=order_details.user_id,
                            user_notification_preference=user_preference.notification_preference,
                            message=UserNotificationMessageType.ORDER_READY,
                        )
                    )
                    break
                case OrderState.ORDER_DECLINED | _:
                    # If the order is declined or in an unexpected state,
                    # then notify the user, and end the workflow
                    workflow.logger.info(
                        "Order declined. order_id=%s. vendor_id=%s", arg.order_id
                    )
                    await notify_user(
                        UserNotificationInput(
                            order_id=arg.order_id,
                            user_id=order_details.user_id,
                            user_notification_preference=user_preference.notification_preference,
                            message=UserNotificationMessageType.ORDER_CANCELED,
                        )
                    )
                    return self.order_state

            self.is_new_state = False
        # end while

        # 6. Wait for the order to be picked up
        await workflow.wait_condition(
            lambda: self.order_state == OrderState.ORDER_PICKED_UP,
        )
        workflow.logger.info(
            "Order completed. order_id=%s. vendor_id=%s",
            arg.order_id,
            order_details.vendor_id,
        )
        await notify_user(
            UserNotificationInput(
                order_id=arg.order_id,
                user_id=order_details.user_id,
                user_notification_preference=user_preference.notification_preference,
                message=UserNotificationMessageType.ORDER_COMPLETED,
            )
        )
        return self.order_state

    @workflow.signal
    def accept_order(self) -> None:
        """
        A signal to accepts an order.
        """
        workflow.logger.info("Accepting an order. state=%s", self.order_state)
        # If the order state can be transitioned, then transition the order state to ORDER_ACCEPTED
        if OrderState.ORDER_ACCEPTED in self.order_state.allowed_next_states:
            self.order_state = OrderState.ORDER_ACCEPTED
            self.is_new_state = True

    @workflow.signal
    def decline_order(self) -> None:
        """
        A signal to decline an order.
        """
        workflow.logger.info("Declining an order. state=%s", self.order_state)
        # If the order state can be transitioned, then transition the order state to ORDER_ACCEPTED
        if OrderState.ORDER_DECLINED in self.order_state.allowed_next_states:
            self.order_state = OrderState.ORDER_DECLINED
            self.is_new_state = True

    @workflow.signal
    def prepare_order(self) -> None:
        """
        A signal to indicate order is being prepared.
        """
        workflow.logger.info(
            "Transitioning an order to preparation. state=%s", self.order_state
        )
        # If the order state can be transitioned, then set the order state to ORDER_PREPARATION
        if OrderState.ORDER_PREPARATION in self.order_state.allowed_next_states:
            self.order_state = OrderState.ORDER_PREPARATION
            self.is_new_state = True

    @workflow.signal
    def ready_order(self) -> None:
        """
        A signal to indicate order is ready.
        """
        workflow.logger.info(
            "Transitioning an order to ready. state=%s",
            self.order_state,
        )
        # If the order state can be transitioned, then set the order state to ORDER_READY
        if OrderState.ORDER_READY in self.order_state.allowed_next_states:
            self.order_state = OrderState.ORDER_READY
            self.is_new_state = True

    @workflow.signal
    def pick_up_order(self) -> None:
        """
        A signal to indicate order is picked up.
        """
        workflow.logger.info(
            "Transitioning an order to picked up. state=%s", self.order_state
        )
        # If the order state can be transitioned, then set the order state to ORDER_COMPLETED
        if OrderState.ORDER_PICKED_UP in self.order_state.allowed_next_states:
            self.order_state = OrderState.ORDER_PICKED_UP
            self.is_new_state = True

    @workflow.query
    def query_order_state(self) -> OrderState:
        """
        Returns the current state of the order.
        """
        return self.order_state

    async def _wait_with_expiration(
        self, f: Callable[[], bool], expiration_time: timedelta
    ) -> timedelta:
        """
        A helper function to wait for a condition with a timeout.
        """
        try:
            await workflow.wait_condition(f, timeout=expiration_time)
        except asyncio.TimeoutError:
            # Given the order has expired, transition order to declined if it is possible
            if OrderState.ORDER_DECLINED in self.order_state.allowed_next_states:
                self.order_state = OrderState.ORDER_DECLINED
            else:
                # If the order cannot be declined (because it has been accepted by vendor),
                # then transition the order to ready
                self.order_state = OrderState.ORDER_READY

            workflow.logger.info(
                "Order expired. Transition to new order state. state=%s",
                self.order_state,
            )

        # Calculate and return the remaining expiration time based on the current time
        remaining_expiration_time = self.order_expiration_time - (
            workflow.now() - workflow.info().start_time
        )
        return remaining_expiration_time
