import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Dict, List

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    import litellm
    from pydantic import BaseModel, ValidationError

    from agents.smolagents.web import WeatherAgent


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatRequest:
    new_user_message: str
    conversation_history: List[ChatMessage]


class ToolArgument(BaseModel):
    name: str
    type: str
    value: str


class Tool(BaseModel):
    name: str
    description: str
    arguments: List[ToolArgument]


TOOLS = [
    Tool(
        name="get_current_weather",
        description="Get the current weather in a location.",
        arguments=[ToolArgument(name="location", type="string", value="")],
    ),
    Tool(
        name="chat",
        description="Default tool to chat with the bot.",
        arguments=[ToolArgument(name="user_prompt", type="string", value="")],
    ),
]


@activity.defn
async def get_tool_activity(user_message: str) -> Tool:
    """
    Activity to get the tools available and determine which tool to use.
    """
    # Create a system prompt that describes the available tools
    tools_description = "Available tools:\n"
    for tool in TOOLS:
        args_desc = ", ".join([f"{arg.name} ({arg.type})" for arg in tool.arguments])
        tools_description += (
            f"- {tool.name}: {tool.description} Arguments: {args_desc}\n"
        )

    # Create messages for the LLM to analyze the user request
    messages = [
        {
            "role": "system",
            "content": f"""You are a tool selection assistant. Given a user request, determine which tool should be used and extract the required arguments.

{tools_description}

Respond with ONLY the tool name and arguments in this exact format:
TOOL: tool_name
ARGS: arg1_value, arg2_value, ...

If no specific tool is needed or the request is just general chat, use the 'chat' tool.
If the user is asking about weather, use the 'get_current_weather' tool and extract the location.""",
        }
    ]

    # Add the new user message
    messages.append({"role": "user", "content": user_message})

    # Call the LLM to determine the tool and arguments
    response = await litellm.acompletion(
        model="openai/gpt-4o",
        messages=messages,
        temperature=0.1,  # Low temperature for more consistent tool selection
        max_tokens=200,
        response_format=Tool,
    )
    tool_response = response.choices[0].message.content.strip()
    try:
        tool = Tool.model_validate_json(tool_response)
    except ValidationError as e:
        activity.logger.error("Error parsing tool response: %s", e)
        # Raise error for Temporal to retry
        raise ValueError("Error parsing tool response.") from e

    return tool


@activity.defn
async def call_llm_activity(request: ChatRequest) -> str:
    """
    Activity to call the LLM using litellm with conversation history.
    """
    # Convert conversation history to the format expected by litellm
    messages = []
    for msg in request.conversation_history:
        messages.append({"role": msg.role, "content": msg.content})

    # Add the new user message
    messages.append({"role": "user", "content": request.new_user_message})

    # Call the LLM using litellm
    response = await litellm.acompletion(
        model="openai/gpt-4o", messages=messages, temperature=0.7, max_tokens=1000
    )

    # Extract the response content
    assistant_response = response.choices[0].message.content

    return assistant_response


@activity.defn
async def get_user_input() -> str:
    """
    Activity to get user input from terminal.

    Please don't use `input` in an activity in production!
    """
    return input("👤 You: ").strip()


@activity.defn
async def get_current_weather(location: str) -> str:
    """
    Activity to get the current weather.
    """
    return WeatherAgent().run(location=location)


@workflow.defn
class WeatherBotWorkflow:
    def __init__(self):
        self.conversation_history: List[ChatMessage] = [
            ChatMessage(
                role="system",
                content="""
                You are a helpful AI assistant. Be friendly and helpful in your responses.
                You cannot answer questions that requires real-time data like the current weather.
                """,
            )
        ]
        self.should_exit = False

    @workflow.run
    async def run(self) -> None:
        """
        Main workflow method that runs a continuous chat session.
        """
        while not self.should_exit:
            user_message = await workflow.execute_activity(
                get_user_input,
                start_to_close_timeout=timedelta(seconds=30),
            )

            workflow.logger.info("User message: %s", user_message)

            if user_message and user_message.lower() == "exit":
                self.should_exit = True
                break

            if user_message:
                tool = await workflow.execute_activity(
                    get_tool_activity,
                    user_message,
                    start_to_close_timeout=timedelta(seconds=10),
                )

                if tool.name == "get_current_weather":
                    tool_response = await workflow.execute_activity(
                        get_current_weather,
                        tool.arguments[0].value,
                        start_to_close_timeout=timedelta(seconds=30),
                    )
                else:  # Default to chat tool
                    tool_response = await workflow.execute_activity(
                        call_llm_activity,
                        ChatRequest(
                            new_user_message=tool.arguments[0].value,
                            conversation_history=self.conversation_history,
                        ),
                        start_to_close_timeout=timedelta(seconds=10),
                    )

                workflow.logger.info("🤖 Weather Bot response: %s", tool_response)

                # Update conversation history
                self.conversation_history.append(
                    ChatMessage(role="user", content=user_message)
                )
                self.conversation_history.append(
                    ChatMessage(role="assistant", content=tool_response)
                )


async def main():
    """
    Main function.
    """
    import logging

    logging.basicConfig(level=logging.INFO)

    # Start client
    client = await Client.connect("localhost:7233")

    TASK_QUEUE = "weather-bot-task-queue"

    # Run a worker for the workflow
    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[WeatherBotWorkflow],
        activities=[
            call_llm_activity,
            get_user_input,
            get_tool_activity,
            get_current_weather,
        ],
        activity_executor=ThreadPoolExecutor(5),
    ):
        await client.execute_workflow(
            WeatherBotWorkflow.run,
            id=f"weather-bot-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )


if __name__ == "__main__":
    asyncio.run(main())
