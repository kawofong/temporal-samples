# Temporal Smolagents Workflows

## Getting started

> Perform the following commands in the project root directory.

1. Install `smolagents` dependencies

    ```bash
    uv sync --group smolagents
    ```

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

1. In a new terminal, use `uv` to run a workflow:

    ```bash
    uv run -m agents.smolagents.current_weather
    ```
