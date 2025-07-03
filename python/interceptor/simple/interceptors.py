"""
Simple Activity Interceptor.
"""

import logging
from typing import Any

import temporalio


class CustomActivityInboundInterceptor(temporalio.worker.ActivityInboundInterceptor):
    """
    A custom activity inbound Interceptor.

    Reference: https://python.temporal.io/temporalio.worker.ActivityInboundInterceptor.html
    """

    def __init__(
        self,
        next: temporalio.worker.ActivityInboundInterceptor,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        super().__init__(next)

    async def execute_activity(
        self, input: temporalio.worker.ExecuteActivityInput
    ) -> Any:
        info = temporalio.activity.info()
        self.logger.info("***** Start inbound interceptor *****")
        self.logger.info("Activity info: %s", info)
        self.logger.info("Input: %s", input)
        result = await super().execute_activity(input)
        self.logger.info("***** End inbound interceptor *****")
        return result


class BasicCustomWorkerInterceptor(temporalio.worker.Interceptor):
    """
    A custom Interceptor that supports worker activities.

    References:

    * https://github.com/temporalio/sdk-python/blob/main/temporalio/contrib/opentelemetry.py
    * https://python.temporal.io/temporalio.client.Interceptor.html
    * https://python.temporal.io/temporalio.worker.Interceptor.html
    """

    def intercept_activity(
        self, next: temporalio.worker.ActivityInboundInterceptor
    ) -> temporalio.worker.ActivityInboundInterceptor:
        """Implementation of `temporalio.worker.Interceptor.intercept_activity`."""
        return CustomActivityInboundInterceptor(next)

    def workflow_interceptor_class(
        self, input: temporalio.worker.WorkflowInterceptorClassInput
    ) -> temporalio.worker.WorkflowInboundInterceptor | None:
        """Implementation of `temporalio.worker.Interceptor.workflow_interceptor_class`."""
        del input  # unused
        return None
