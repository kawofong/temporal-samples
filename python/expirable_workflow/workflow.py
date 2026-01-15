"""
Expirable Payment Workflow.

This workflow demonstrates how to implement a self-cancelling workflow
that expires after a specified duration using a Timer racing against
the main business logic.
"""

import asyncio
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError, CancelledError

with workflow.unsafe.imports_passed_through():
    from python.expirable_workflow.activities import (
        accept_payment,
        check_fraud,
        notify_customer,
        validate_payment,
    )
    from python.expirable_workflow.schemas import (
        PaymentStatus,
        PaymentWorkflowInput,
        PaymentWorkflowResult,
    )


@workflow.defn
class ExpirablePaymentWorkflow:
    """
    A payment workflow that automatically cancels itself after a specified duration.

    The workflow:
    1. Starts a Timer with the expiration duration
    2. In parallel, processes the payment (validate, fraud check, accept, notify)
    3. If the Timer fires before payment completes, the workflow cancels itself
    """

    @workflow.init
    def __init__(self, input: PaymentWorkflowInput) -> None:
        self.payment_id = input.payment_id
        self.amount = input.amount
        self.expire_in = input.expire_in
        self.status = PaymentStatus.PENDING
        self.is_expired = False

    @workflow.run
    async def run(self, input: PaymentWorkflowInput) -> PaymentWorkflowResult:
        """
        Main workflow execution.

        Races the payment processing against an expiration timer.
        If the timer wins, the workflow cancels itself.
        """
        workflow.logger.info(
            "Starting expirable payment workflow. payment_id=%s, expire_in=%d seconds",
            self.payment_id,
            self.expire_in,
        )

        # Create the payment processing task
        payment_task = asyncio.create_task(self._process_payment())

        # Create the expiration timer task
        expiration_task = asyncio.create_task(self._expiration_timer())

        # Race the two tasks - wait for whichever completes first
        done, pending = await asyncio.wait(
            [payment_task, expiration_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        # Cancel any pending tasks
        for task in pending:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        if expiration_task in done:
            self.is_expired = True
            workflow.logger.warning(
                "Payment workflow expired. payment_id=%s", self.payment_id
            )
            return PaymentWorkflowResult(
                payment_id=self.payment_id,
                status=self.status,
                message="Payment workflow expired",
            )

        return payment_task.result()

    async def _expiration_timer(self) -> None:
        """
        Timer that fires after the expiration duration.
        """
        workflow.logger.info(
            "Expiration timer started. payment_id=%s, expire_in=%d seconds",
            self.payment_id,
            self.expire_in,
        )
        await asyncio.sleep(self.expire_in)
        workflow.logger.info("Expiration timer fired! payment_id=%s", self.payment_id)

    async def _process_payment(self) -> PaymentWorkflowResult:
        """
        Main payment processing logic.

        Steps:
        1. Validate payment
        2. Check for fraud
        3. Accept payment
        4. Notify customer
        """
        retry_policy = RetryPolicy(
            maximum_interval=timedelta(seconds=5),
        )
        try:
            self.status = PaymentStatus.VALIDATING
            workflow.logger.info(
                "Step 1: Validating payment. payment_id=%s", self.payment_id
            )
            is_valid = await workflow.execute_activity(
                validate_payment,
                args=[self.payment_id, self.amount],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            if not is_valid:
                self.status = PaymentStatus.CANCELLED
                return PaymentWorkflowResult(
                    payment_id=self.payment_id,
                    status=self.status,
                    message="Payment validation failed",
                )

            self.status = PaymentStatus.FRAUD_CHECK
            workflow.logger.info(
                "Step 2: Checking for fraud. payment_id=%s", self.payment_id
            )
            is_not_fraudulent = await workflow.execute_activity(
                check_fraud,
                args=[self.payment_id, self.amount],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            if not is_not_fraudulent:
                self.status = PaymentStatus.CANCELLED
                return PaymentWorkflowResult(
                    payment_id=self.payment_id,
                    status=self.status,
                    message="Payment flagged as potentially fraudulent",
                )

            self.status = PaymentStatus.ACCEPTED
            workflow.logger.info(
                "Step 3: Accepting payment. payment_id=%s", self.payment_id
            )
            transaction_id = await workflow.execute_activity(
                accept_payment,
                args=[self.payment_id, self.amount],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            self.status = PaymentStatus.NOTIFIED
            workflow.logger.info(
                "Step 4: Notifying customer. payment_id=%s", self.payment_id
            )
            await workflow.execute_activity(
                notify_customer,
                args=[self.payment_id, transaction_id],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            self.status = PaymentStatus.COMPLETED
            workflow.logger.info(
                "Payment workflow completed successfully. payment_id=%s, transaction_id=%s",
                self.payment_id,
                transaction_id,
            )

            return PaymentWorkflowResult(
                payment_id=self.payment_id,
                status=self.status,
                message=f"Payment completed successfully. Transaction ID: {transaction_id}",
            )
        except asyncio.CancelledError:
            self.status = PaymentStatus.CANCELLED
            workflow.logger.warning(
                "Payment workflow cancelled. payment_id=%s", self.payment_id
            )
        except ActivityError as e:
            if isinstance(e.cause, CancelledError):
                self.status = PaymentStatus.CANCELLED
                workflow.logger.warning(
                    "Payment workflow cancelled. payment_id=%s", self.payment_id
                )
            else:
                raise e

    @workflow.query
    def get_status(self) -> PaymentStatus:
        """
        Query to get the current payment status.
        """
        return self.status

    @workflow.query
    def is_workflow_expired(self) -> bool:
        """
        Query to check if the workflow has expired.
        """
        return self.is_expired
