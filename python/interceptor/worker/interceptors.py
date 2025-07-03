"""
Simple Activity Interceptor.
"""

import logging
from typing import Any, Type

import temporalio


class CustomActivityOutboundInterceptor(temporalio.worker.ActivityOutboundInterceptor):
    """
    A custom activity outbound interceptor.

    Reference: https://python.temporal.io/temporalio.worker.ActivityOutboundInterceptor.html
    """

    def __init__(
        self,
        next: temporalio.worker.ActivityOutboundInterceptor,
    ) -> None:
        self.logger = logging.getLogger(__name__)
        super().__init__(next)

    def info(self) -> temporalio.activity.Info:
        self.logger.info(">>>>> Start Activity Info interceptor >>>>>")
        info = super().info()
        self.logger.info("Activity info: %s", info)
        self.logger.info("<<<<< End Activity Info interceptor <<<<<")
        return info

    def heartbeat(self, *details: Any) -> None:
        self.logger.info(">>>>> Start Activity Heartbeat interceptor >>>>>")
        self.logger.info("Heartbeat details: %s", details)
        super().heartbeat(*details)
        self.logger.info("<<<<< End Activity Heartbeat interceptor <<<<<")


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

    def init(self, outbound: temporalio.worker.ActivityOutboundInterceptor) -> None:
        self.next.init(CustomActivityOutboundInterceptor(outbound))

    async def execute_activity(
        self, input: temporalio.worker.ExecuteActivityInput
    ) -> Any:
        self.logger.info(">>>>> Start execute Activity interceptor >>>>>")
        self.logger.info("Input: %s", input)
        result = await super().execute_activity(input)
        self.logger.info("<<<<< End execute Activity interceptor <<<<<")
        return result


###


class CustomWorkflowOutboundInterceptor(temporalio.worker.WorkflowOutboundInterceptor):
    """
    A custom Workflow outbound interceptor.

    Reference: https://python.temporal.io/temporalio.worker.WorkflowOutboundInterceptor.html
    """

    def __init__(
        self,
        next: temporalio.worker.WorkflowOutboundInterceptor,
    ) -> None:
        super().__init__(next)
        self.logger = logging.getLogger(__name__)

    def continue_as_new(self, input: temporalio.worker.ContinueAsNewInput) -> None:
        self.logger.info(">>>>> Start continue as new interceptor >>>>>")
        self.logger.info("Continue as new input: %s", input)
        super().continue_as_new(input)
        self.logger.info("<<<<< End continue as new interceptor <<<<<")

    async def signal_child_workflow(
        self, input: temporalio.worker.SignalChildWorkflowInput
    ) -> None:
        self.logger.info(">>>>> Start signal child workflow interceptor >>>>>")
        self.logger.info("Signal child workflow input: %s", input)
        await super().signal_child_workflow(input)
        self.logger.info("<<<<< End signal child workflow interceptor <<<<<")

    async def signal_external_workflow(
        self, input: temporalio.worker.SignalExternalWorkflowInput
    ) -> None:
        self.logger.info(">>>>> Start signal external workflow interceptor >>>>>")
        self.logger.info("Signal external workflow input: %s", input)
        await super().signal_external_workflow(input)
        self.logger.info("<<<<< End signal external workflow interceptor <<<<<")

    def start_activity(
        self, input: temporalio.worker.StartActivityInput
    ) -> temporalio.workflow.ActivityHandle:
        self.logger.info(">>>>> Start start activity interceptor >>>>>")
        self.logger.info("Start activity input: %s", input)
        result = super().start_activity(input)
        self.logger.info("<<<<< End start activity interceptor <<<<<")
        return result

    async def start_child_workflow(
        self, input: temporalio.worker.StartChildWorkflowInput
    ) -> temporalio.workflow.ChildWorkflowHandle:
        self.logger.info(">>>>> Start start child workflow interceptor >>>>>")
        self.logger.info("Start child workflow input: %s", input)
        result = await super().start_child_workflow(input)
        self.logger.info("<<<<< End start child workflow interceptor <<<<<")
        return result

    def start_local_activity(
        self, input: temporalio.worker.StartLocalActivityInput
    ) -> temporalio.workflow.ActivityHandle:
        self.logger.info(">>>>> Start start local activity interceptor >>>>>")
        self.logger.info("Start local activity input: %s", input)
        result = super().start_local_activity(input)
        self.logger.info("<<<<< End start local activity interceptor <<<<<")
        return result


class CustomWorkflowInboundInterceptor(temporalio.worker.WorkflowInboundInterceptor):
    """
    A custom Workflow inbound interceptor.

    Reference: https://python.temporal.io/temporalio.worker.WorkflowInboundInterceptor.html
    """

    def __init__(self, next: temporalio.worker.WorkflowInboundInterceptor) -> None:
        self.logger = logging.getLogger(__name__)
        super().__init__(next)

    def init(self, outbound: temporalio.worker.WorkflowOutboundInterceptor) -> None:
        """Implementation of
        :py:meth:`temporalio.worker.WorkflowInboundInterceptor.init`.
        """
        super().init(CustomWorkflowOutboundInterceptor(outbound))

    async def execute_workflow(
        self, input: temporalio.worker.ExecuteWorkflowInput
    ) -> Any:
        """Implementation of `temporalio.worker.WorkflowInboundInterceptor.execute_workflow`."""
        self.logger.info(">>>>> Start execute Workflow interceptor >>>>>")
        self.logger.info("Input: %s", input)
        result = await super().execute_workflow(input)
        self.logger.info("<<<<< End execute Workflow interceptor <<<<<")
        return result

    async def handle_signal(self, input: temporalio.worker.HandleSignalInput) -> None:
        """Implementation of `temporalio.worker.WorkflowInboundInterceptor.handle_signal`."""
        self.logger.info(">>>>> Start handle Signal interceptor >>>>>")
        self.logger.info("Input: %s", input)
        await super().handle_signal(input)
        self.logger.info("<<<<< End handle Signal interceptor <<<<<")

    async def handle_query(self, input: temporalio.worker.HandleQueryInput) -> Any:
        """Implementation of `temporalio.worker.WorkflowInboundInterceptor.handle_query`."""
        self.logger.info(">>>>> Start handle Query interceptor >>>>>")
        self.logger.info("Input: %s", input)
        result = await super().handle_query(input)
        self.logger.info("<<<<< End handle Query interceptor <<<<<")
        return result

    def handle_update_validator(
        self, input: temporalio.worker.HandleUpdateInput
    ) -> None:
        """Implementation of `temporalio.worker.WorkflowInboundInterceptor.handle_update_validator`."""
        self.logger.info(">>>>> Start handle Update Validator interceptor >>>>>")
        self.logger.info("Input: %s", input)
        super().handle_update_validator(input)
        self.logger.info("<<<<< End handle Update Validator interceptor <<<<<")

    async def handle_update_handler(
        self, input: temporalio.worker.HandleUpdateInput
    ) -> Any:
        """Implementation of `temporalio.worker.WorkflowInboundInterceptor.handle_update_handler`."""
        self.logger.info(">>>>> Start handle Update Handler interceptor >>>>>")
        self.logger.info("Input: %s", input)
        result = await super().handle_update_handler(input)
        self.logger.info("<<<<< End handle Update Handler interceptor <<<<<")
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
    ) -> Type[temporalio.worker.WorkflowInboundInterceptor]:
        """Implementation of `temporalio.worker.Interceptor.workflow_interceptor_class`."""
        print("Workflow interceptor class input: %s", input)
        return CustomWorkflowInboundInterceptor
