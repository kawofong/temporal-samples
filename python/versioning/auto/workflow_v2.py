"""
A basic workflow to demonstrate Worker Versioning.

Reference: https://docs.temporal.io/production-deployment/worker-deployments/worker-versioning

To run this Workflow, see `python.versioning.basic.workflow.py`.
"""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy, SearchAttributeKey, VersioningBehavior

with workflow.unsafe.imports_passed_through():
    from python.versioning.auto.activities import (
        deposit,
        notify_user,
        validate_transfer,
        withdraw,
    )


@workflow.defn(
    name="MoneyTransferWorkflow", versioning_behavior=VersioningBehavior.AUTO_UPGRADE
)
class MoneyTransferWorkflowV2:
    """
    A basic workflow that transfers money between two accounts.
    """

    WORKFLOW_STEP = SearchAttributeKey.for_keyword("Step")

    @workflow.run
    async def run(self) -> None:
        """
        Workflow runner.
        """
        workflow_id = workflow.info().workflow_id

        # Because this workflow is configured to auto-upgrade, open Workflow Executions
        # will be upgraded to the new build version automatically.
        # If your new Workflow Definition contains non-deterministic behavior,
        # auto-upgrade may cause non-deterministic errors (NDEs).
        # In this case, you should use the `VersioningBehavior.PINNED` mode instead.
        if workflow.patched("notify_user"):
            workflow.upsert_search_attributes(
                [self.WORKFLOW_STEP.value_set("NOTIFYING")]
            )
            await workflow.execute_activity(
                notify_user,
                workflow_id,
                start_to_close_timeout=timedelta(seconds=10),
                retry_policy=RetryPolicy(
                    maximum_interval=timedelta(seconds=1),
                ),
            )

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("VALIDATING")])
        await workflow.execute_activity(
            validate_transfer,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("WITHDRAWING")])
        await workflow.execute_activity(
            withdraw,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )

        workflow.upsert_search_attributes([self.WORKFLOW_STEP.value_set("DEPOSITING")])
        await workflow.execute_activity(
            deposit,
            workflow_id,
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                maximum_interval=timedelta(seconds=1),
            ),
        )
