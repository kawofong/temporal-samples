"""
Workflow starter for the expirable payment workflow.

This script demonstrates starting the workflow with different expiration times:
- A workflow that completes before expiration
- A workflow that expires before completion
"""

import asyncio
import logging
import uuid

from temporalio.client import WorkflowFailureError
from temporalio.exceptions import CancelledError

from common.python.client import TemporalClientFactory
from python.expirable_workflow.schemas import (
    PaymentWorkflowInput,
    PaymentWorkflowResult,
)
from python.expirable_workflow.worker import TASK_QUEUE
from python.expirable_workflow.workflow import ExpirablePaymentWorkflow


async def run_workflow(
    expire_in: int, payment_id: str | None = None, amount: float = 100.0
) -> None:
    """
    Start and run an expirable payment workflow.

    Args:
        expire_in: Number of seconds until the workflow expires
        payment_id: Optional payment ID (generated if not provided)
        amount: Payment amount
    """
    client = await TemporalClientFactory.create_client()

    if payment_id is None:
        payment_id = f"PAY-{uuid.uuid4().hex[:8]}"

    workflow_input = PaymentWorkflowInput(
        payment_id=payment_id,
        amount=amount,
        expire_in=expire_in,
    )

    print(f"\n{'='*60}")
    print(f"Starting workflow: {payment_id}")
    print(f"Amount: ${amount:.2f}")
    print(f"Expiration: {expire_in} seconds")
    print(f"{'='*60}\n")

    try:
        result: PaymentWorkflowResult = await client.execute_workflow(
            ExpirablePaymentWorkflow.run,
            workflow_input,
            id=f"expirable-payment-{payment_id}",
            task_queue=TASK_QUEUE,
        )
        print(f"\n{'='*60}")
        print(f"Workflow completed!")
        print(f"Payment ID: {result.payment_id}")
        print(f"Status: {result.status}")
        print(f"Message: {result.message}")
        print(f"{'='*60}\n")

    except WorkflowFailureError as e:
        if isinstance(e.cause, CancelledError):
            print(f"\n{'='*60}")
            print(f"Workflow expired/cancelled!")
            print(f"Payment ID: {payment_id}")
            print(f"Reason: {e.cause}")
            print(f"{'='*60}\n")
        else:
            raise


async def demo_successful_completion():
    """
    Demo: Workflow completes before expiration.

    The payment processing takes ~4 seconds total, so with a 10-second
    expiration, it should complete successfully.
    """
    print("\n" + "=" * 60)
    print("DEMO 1: Workflow that completes before expiration")
    print("=" * 60)
    await run_workflow(expire_in=10, amount=100.0)


async def demo_expiration():
    """
    Demo: Workflow expires before completion.

    The payment processing takes ~4 seconds total, so with a 3-second
    expiration, it should expire before completing.
    """
    print("\n" + "=" * 60)
    print("DEMO 2: Workflow that expires before completion")
    print("=" * 60)
    await run_workflow(expire_in=3, amount=100.0)


async def main():
    logging.basicConfig(level=logging.INFO)

    print("\n" + "#" * 60)
    print("# Expirable Payment Workflow Demo")
    print("#" * 60)

    await demo_successful_completion()

    await demo_expiration()


if __name__ == "__main__":
    asyncio.run(main())
