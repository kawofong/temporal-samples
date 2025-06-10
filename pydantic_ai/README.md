# Temporal Pydantic.ai Workflows

## Getting started

1. Copy `.envrc.example`

    ```bash
    cp .envrc.example .envrc
    ```

1. Obtain an OpenAI API key and set `OPENAI_API_KEY` in `.envrc`

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

1. In a new terminal, use `uv` to run a workflow runner:

    ```bash
    uv run pydantic_ai/pydantic_ai_hello.py
    ```
