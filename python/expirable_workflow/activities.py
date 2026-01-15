"""
Payment processing activities for the expirable workflow.
"""

import asyncio

from temporalio import activity


@activity.defn
async def validate_payment(payment_id: str, amount: float) -> bool:
    """
    Validates the payment details.
    """
    activity.logger.info(
        "Validating payment. payment_id=%s, amount=%.2f", payment_id, amount
    )
    # Simulate validation processing time
    await asyncio.sleep(1)

    # Simulate validation logic (in real world, check card details, balance, etc.)
    is_valid = amount > 0 and amount < 10000
    activity.logger.info(
        "Payment validation complete. payment_id=%s, is_valid=%s", payment_id, is_valid
    )
    return is_valid


@activity.defn
async def check_fraud(payment_id: str, amount: float) -> bool:
    """
    Performs fraud detection on the payment.
    """
    activity.logger.info(
        "Checking for fraud. payment_id=%s, amount=%.2f", payment_id, amount
    )
    # Simulate fraud check processing time
    await asyncio.sleep(1)

    # Simulate fraud detection (in real world, use ML models, rules, etc.)
    is_fraudulent = amount > 5000  # Simple rule: flag large amounts
    activity.logger.info(
        "Fraud check complete. payment_id=%s, is_fraudulent=%s",
        payment_id,
        is_fraudulent,
    )
    return not is_fraudulent  # Return True if NOT fraudulent


@activity.defn
async def accept_payment(payment_id: str, amount: float) -> str:
    """
    Accepts and processes the payment.
    """
    activity.logger.info(
        "Accepting payment. payment_id=%s, amount=%.2f", payment_id, amount
    )
    # Simulate payment processing time
    await asyncio.sleep(1)

    # Generate a transaction ID
    transaction_id = f"TXN-{payment_id}-{int(amount * 100)}"
    activity.logger.info(
        "Payment accepted. payment_id=%s, transaction_id=%s", payment_id, transaction_id
    )
    return transaction_id


@activity.defn
async def notify_customer(payment_id: str, transaction_id: str) -> None:
    """
    Notifies the customer about the payment result.
    """
    activity.logger.info(
        "Notifying customer. payment_id=%s, transaction_id=%s",
        payment_id,
        transaction_id,
    )
    # Simulate notification sending time
    await asyncio.sleep(1)

    activity.logger.info(
        "Customer notified successfully. payment_id=%s, transaction_id=%s",
        payment_id,
        transaction_id,
    )
