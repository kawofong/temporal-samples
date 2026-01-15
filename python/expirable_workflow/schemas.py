"""
Schemas for the expirable payment workflow.
"""

from dataclasses import dataclass
from enum import Enum


class PaymentStatus(str, Enum):
    """Payment processing status."""

    PENDING = "PENDING"
    VALIDATING = "VALIDATING"
    FRAUD_CHECK = "FRAUD_CHECK"
    ACCEPTED = "ACCEPTED"
    NOTIFIED = "NOTIFIED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


@dataclass
class PaymentWorkflowInput:
    """Input for the expirable payment workflow."""

    payment_id: str
    amount: float
    # Number of seconds until the workflow expires, 5 seconds by default
    expire_in: int = 5


@dataclass
class PaymentWorkflowResult:
    """Result of the expirable payment workflow."""

    payment_id: str
    status: PaymentStatus
    message: str
