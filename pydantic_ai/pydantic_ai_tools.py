"""
Reference: https://ai.pydantic.dev/examples/bank-support/

Shows tools and dependency injection from Pydantic AI.
"""

import asyncio
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from pydantic import BaseModel, Field

    from pydantic_ai import Agent, RunContext


class DatabaseConn:
    """This is a fake database for example purposes.

    In reality, you'd be connecting to an external database
    (e.g. PostgreSQL) to get information about customers.
    """

    @classmethod
    async def customer_name(cls, *, account_id: int) -> str | None:
        """
        Get the customer name of a bank account.
        """
        if account_id == 123:
            return "John"
        if account_id == 456:
            return "Adam"
        return None

    @classmethod
    async def customer_balance(cls, *, account_id: int, include_pending: bool) -> float:
        """
        Get the balance of a bank account.
        """
        if account_id == 123 and include_pending:
            return 123.45
        else:
            raise ValueError("Customer not found")


@dataclass
class SupportDependencies:
    """
    Support agent dependencies.
    """

    customer_id: int
    db: DatabaseConn


class SupportOutput(BaseModel):
    """
    Support agent output.
    """

    support_advice: str = Field(description="Advice returned to the customer")
    block_card: bool = Field(description="Whether to block their card or not")
    risk: int = Field(description="Risk level of query", ge=0, le=10)


@dataclass
class RunSupportAgentInput:
    """
    Run support agent input.
    """

    query: str
    customer_id: int


@dataclass
class RunQueryInput(RunSupportAgentInput):
    """
    Run support agent query input.
    """


class SupportAgentActivities:
    """
    Support agent activities.
    """

    def __init__(self):
        self._support_agent = Agent(
            "openai:gpt-4o",
            deps_type=SupportDependencies,
            output_type=SupportOutput,
            system_prompt=(
                "You are a support agent in our bank, give the "
                "customer support and judge the risk level of their query. "
                "Always greet and address the customer by name in your response."
            ),
        )

        @self._support_agent.system_prompt
        async def add_customer_name(ctx: RunContext[SupportDependencies]) -> str:
            customer_name = await ctx.deps.db.customer_name(
                account_id=ctx.deps.customer_id
            )
            return f"The customer's name is {customer_name}!"

        @self._support_agent.tool
        async def customer_balance(
            ctx: RunContext[SupportDependencies], include_pending: bool
        ) -> str:
            """Returns the customer's current account balance."""
            balance = await ctx.deps.db.customer_balance(
                account_id=ctx.deps.customer_id,
                include_pending=include_pending,
            )
            return f"${balance:.2f}"

    @activity.defn
    def run_query(self, arg: RunQueryInput) -> SupportOutput:
        """
        Ask the agent a question.
        """
        activity.logger.info("Running agent with question %s" % arg.query)
        deps = SupportDependencies(customer_id=arg.customer_id, db=DatabaseConn())
        result = self._support_agent.run_sync(arg.query, deps=deps)
        return result.output


@workflow.defn
class SupportAgentWorkflow:
    """
    Support agent workflow for a bank.
    """

    @workflow.run
    async def run(self) -> SupportOutput:
        workflow.logger.info("Running support agent workflow")

        balance_result: SupportOutput = await workflow.execute_activity(
            SupportAgentActivities.run_query,
            RunQueryInput(query="What is my balance?", customer_id=123),
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("Support agent workflow result: %s", balance_result)

        lost_card_result: SupportOutput = await workflow.execute_activity(
            SupportAgentActivities.run_query,
            RunQueryInput(query="I just lost my card!", customer_id=456),
            start_to_close_timeout=timedelta(seconds=10),
        )
        workflow.logger.info("Support agent workflow result: %s", lost_card_result)


async def main():
    """
    Main function.
    """
    import logging

    logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233")

    TASK_QUEUE = "pydantic-ai-support-agent-task-queue"

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SupportAgentWorkflow],
        activities=[SupportAgentActivities().run_query],
        activity_executor=ThreadPoolExecutor(5),
    ):
        await client.execute_workflow(
            SupportAgentWorkflow.run,
            id=f"pydantic-ai-support-agent-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


if __name__ == "__main__":
    asyncio.run(main())
