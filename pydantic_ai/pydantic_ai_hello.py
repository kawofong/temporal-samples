"""
Reference: https://ai.pydantic.dev/#hello-world-example

```
from pydantic_ai import Agent

agent = Agent(
    "openai:gpt-4o",
    system_prompt="Be concise, reply with one sentence.",
)

result = agent.run_sync('Where does "hello world" come from?')
print(result.output)
```
"""

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from pydantic_ai import Agent


@dataclass
class RunAgentInput:
    """
    Run agent input.
    """

    question: str


@dataclass
class HelloWorkflowInput:
    """
    Hello workflow input.
    """

    question: str


class AgentActivities:
    """
    Agent activities.
    """

    def __init__(self):
        self._agent = Agent(
            "openai:gpt-4o",
            system_prompt="Be concise, reply with one sentence.",
        )

    @activity.defn
    def run_agent(self, arg: RunAgentInput) -> str:
        """
        Ask the agent a question.
        """
        activity.logger.info("Running agent with question %s" % arg.question)
        result = self._agent.run_sync(arg.question)
        return result.output


@workflow.defn
class PydanticAiHelloWorkflow:
    """
    Pydantic AI "Hello World" Workflow.
    """

    @workflow.run
    async def run(self, arg: HelloWorkflowInput) -> str:
        workflow.logger.info("Running workflow with parameter %s" % arg.question)

        return await workflow.execute_activity(
            AgentActivities.run_agent,
            RunAgentInput(arg.question),
            start_to_close_timeout=timedelta(seconds=10),
        )


async def main():
    """
    Main function.
    """
    import logging

    logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233")

    TASK_QUEUE = "pydantic-ai-hello-world-task-queue"
    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[PydanticAiHelloWorkflow],
        activities=[AgentActivities().run_agent],
        activity_executor=ThreadPoolExecutor(5),
    ):
        result = await client.execute_workflow(
            PydanticAiHelloWorkflow.run,
            HelloWorkflowInput(question='Where does "hello world" come from?'),
            id="pydantic-ai-hello-world-workflow-id",
            task_queue=TASK_QUEUE,
        )
        print(f"Result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
