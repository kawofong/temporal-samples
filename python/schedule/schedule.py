"""
Create a Temporal Schedule that runs ShipOrderWorkflow every day at noon UTC.

The schedule is idempotent: running this script again when a schedule with the
same ID already exists will log a message and exit cleanly.

Supports local dev server and Temporal Cloud via environment variables:

    TEMPORAL_ADDRESS    Server address (default: localhost:7233)
    TEMPORAL_NAMESPACE  Namespace (default: default)
    TEMPORAL_API_KEY    API key - when set, enables TLS and targets Temporal Cloud

To create the schedule against the local dev server:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, create the schedule:

    ```bash
    uv run poe create_schedule
    ```

3. Inspect or manage the schedule:

    ```bash
    temporal schedule describe --schedule-id daily-ship-orders
    temporal schedule trigger  --schedule-id daily-ship-orders
    temporal schedule delete   --schedule-id daily-ship-orders
    ```
"""

import asyncio
import logging
import os

from temporalio.client import (
    Client,
    Schedule,
    ScheduleActionStartWorkflow,
    ScheduleAlreadyRunningError,
    ScheduleCalendarSpec,
    ScheduleOverlapPolicy,
    SchedulePolicy,
    ScheduleRange,
    ScheduleSpec,
    ScheduleState,
)

from python.schedule.parallel_activities import TASK_QUEUE, ShipOrderWorkflow

SCHEDULE_ID = "daily-ship-orders"
WORKFLOW_ID = "daily-ship-orders-workflow"


async def connect_client() -> Client:
    """
    Connect to Temporal using environment variables.

    When TEMPORAL_API_KEY is set the client connects to Temporal Cloud with TLS
    and API-key authentication. Otherwise it connects to the local dev server.
    """
    address = os.environ.get("TEMPORAL_ADDRESS", "localhost:7233")
    namespace = os.environ.get("TEMPORAL_NAMESPACE", "default")
    api_key = os.environ.get("TEMPORAL_API_KEY")

    if api_key:
        logging.getLogger(__name__).info(
            "Connecting to Temporal Cloud at %s (namespace=%s)", address, namespace
        )
        return await Client.connect(
            address,
            namespace=namespace,
            api_key=api_key,
            tls=True,
        )

    logging.getLogger(__name__).info(
        "Connecting to local dev server at %s (namespace=%s)", address, namespace
    )
    return await Client.connect(address, namespace=namespace)


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    client = await connect_client()

    schedule = Schedule(
        action=ScheduleActionStartWorkflow(
            ShipOrderWorkflow.run,
            id=WORKFLOW_ID,
            task_queue=TASK_QUEUE,
        ),
        spec=ScheduleSpec(
            # Fire every day at 12:00:00 UTC.
            calendars=[
                ScheduleCalendarSpec(
                    hour=[ScheduleRange(12)],
                    minute=[ScheduleRange(0)],
                    second=[ScheduleRange(0)],
                )
            ],
            time_zone_name="UTC",
        ),
        policy=SchedulePolicy(
            # Skip the new run if the previous day's execution is still in progress.
            overlap=ScheduleOverlapPolicy.BUFFER_ALL,
        ),
        state=ScheduleState(
            note="Ships orders every day at noon UTC.",
        ),
    )

    try:
        handle = await client.create_schedule(SCHEDULE_ID, schedule)
        logger.info(
            "Schedule '%s' created — next run at noon UTC. Handle: %s",
            SCHEDULE_ID,
            handle.id,
        )
    except ScheduleAlreadyRunningError:
        logger.info(
            "Schedule '%s' already exists — nothing to do. "
            "Use `temporal schedule describe --schedule-id %s` to inspect it.",
            SCHEDULE_ID,
            SCHEDULE_ID,
        )


if __name__ == "__main__":
    asyncio.run(main())
