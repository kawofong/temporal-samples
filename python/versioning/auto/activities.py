import time

from temporalio import activity


@activity.defn
def validate_transfer(workflow_id: str) -> None:
    """
    A basic activity that validates a transfer.
    """
    activity.logger.info("Validating transfer. workflow_id: %s", workflow_id)
    time.sleep(1)
    activity.logger.info("Transfer validated. workflow_id: %s", workflow_id)


@activity.defn
def withdraw(workflow_id: str) -> None:
    """
    A basic activity that withdraws money from an account.
    """
    activity.logger.info("Withdrawing money from account. workflow_id: %s", workflow_id)
    time.sleep(4)
    activity.logger.info("Money withdrawn. workflow_id: %s", workflow_id)


@activity.defn
def deposit(workflow_id: str) -> None:
    """
    A basic activity that deposits money into an account.
    """
    activity.logger.info("Depositing money into account. workflow_id: %s", workflow_id)
    time.sleep(4)
    activity.logger.info("Money deposited. workflow_id: %s", workflow_id)


@activity.defn
def notify_user(workflow_id: str) -> None:
    """
    A basic activity that notifies the user.
    """
    activity.logger.info("Notifying user. workflow_id: %s", workflow_id)
    time.sleep(2)
    activity.logger.info("User notified. workflow_id: %s", workflow_id)
