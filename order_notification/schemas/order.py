"""
Schema for order notification workflow.
"""

from datetime import datetime
from enum import StrEnum
from typing import List

from pydantic import BaseModel


class OrderState(StrEnum):
    """
    Enum representing different states of an order.
    """

    ORDER_PLACED = "ORDER_PLACED"
    VENDOR_NOTIFIED = "VENDOR_NOTIFIED"
    ORDER_ACCEPTED = "ORDER_ACCEPTED"
    ORDER_DECLINED = "ORDER_DECLINED"
    ORDER_PREPARATION = "ORDER_PREPARATION"
    ORDER_READY = "ORDER_READY"
    ORDER_PICKED_UP = "ORDER_PICKED_UP"

    @property
    def description(self) -> str:
        """Returns a human-readable description of the state."""
        return _STATE_DESCRIPTIONS.get(self, "Unknown state")

    @property
    def is_terminal_state(self) -> bool:
        """Checks if the current state is a terminal state."""
        return self in {OrderState.ORDER_PICKED_UP, OrderState.ORDER_DECLINED}

    @property
    def requires_vendor_action(self) -> bool:
        """Checks if the current state requires vendor action."""
        return self in {
            OrderState.VENDOR_NOTIFIED,
            OrderState.ORDER_PREPARATION,
            OrderState.ORDER_READY,
        }

    @property
    def allowed_next_states(self) -> List["OrderState"]:
        """Returns a list of valid next states from the current state."""
        return _STATE_TRANSITIONS.get(self, [])

    def can_transition_to(self, next_state: "OrderState") -> bool:
        """
        Checks if transitioning to the given state is valid.

        Args:
            next_state: The state to transition to

        Returns:
            bool: Whether the transition is valid
        """
        return next_state in self.allowed_next_states


# State descriptions for human-readable output
_STATE_DESCRIPTIONS = {
    OrderState.ORDER_PLACED: "Order has been placed by the customer",
    OrderState.VENDOR_NOTIFIED: "Restaurant has been notified of the new order",
    OrderState.ORDER_ACCEPTED: "Restaurant has accepted the order",
    OrderState.ORDER_DECLINED: "Restaurant has declined the order",
    OrderState.ORDER_PREPARATION: "Order is being prepared by the restaurant",
    OrderState.ORDER_READY: "Order is ready for pickup",
    OrderState.ORDER_PICKED_UP: "Order has been picked up to the customer",
}

# Valid state transitions
_STATE_TRANSITIONS = {
    OrderState.ORDER_PLACED: [OrderState.VENDOR_NOTIFIED],
    OrderState.VENDOR_NOTIFIED: [
        OrderState.ORDER_ACCEPTED,
        OrderState.ORDER_DECLINED,
    ],
    OrderState.ORDER_ACCEPTED: [OrderState.ORDER_PREPARATION],
    OrderState.ORDER_PREPARATION: [OrderState.ORDER_READY],
    OrderState.ORDER_READY: [OrderState.ORDER_PICKED_UP],
    OrderState.ORDER_PICKED_UP: [],  # Terminal state
    OrderState.ORDER_DECLINED: [],  # Terminal state
}


class OrderWorkflowInput(BaseModel):
    """
    Input for the order workflow.
    """

    order_id: str
    expiration_time: int = 60  # in seconds; 1 minute expiration time by default


class OrderDetails(BaseModel):
    """
    Order details.
    """

    order_id: str
    user_id: str
    vendor_id: str
    order_date: datetime
