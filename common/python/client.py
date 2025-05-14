"""
Temporal Cloud client.
"""

import os
from pathlib import Path

from temporalio.client import Client, TLSConfig
from temporalio.contrib.pydantic import pydantic_data_converter

from common.python.constants import CERT_DIR


class TemporalCloudClient:
    """
    Temporal Cloud client.
    """

    def __init__(
        self,
        namespace: str,
        cert_path: Path,
        key_path: Path,
        account_id: str = "a2dd6",
    ):
        self.namespace_id = f"{namespace}.{account_id}"
        self.endpoint = f"{self.namespace_id}.tmprl.cloud:7233"
        self.cert_path = cert_path
        self.key_path = key_path

    async def connect(self) -> Client:
        """
        Create a Temporal client to Temporal Cloud.
        """
        with open(self.cert_path, "rb") as cert_file:
            client_cert = cert_file.read()
        with open(self.key_path, "rb") as key_file:
            client_private_key = key_file.read()
        client = await Client.connect(
            self.endpoint,
            namespace=self.namespace_id,
            tls=TLSConfig(
                client_cert=client_cert,
                client_private_key=client_private_key,
            ),
            data_converter=pydantic_data_converter,
        )
        return client


class TemporalDevClient:
    """
    Temporal Dev client.
    """

    def __init__(self, namespace="default"):
        self.endpoint = "localhost:7233"
        self.namespace_id = namespace

    async def connect(self) -> Client:
        """
        Create a Temporal client to Temporal Dev.
        """
        client = await Client.connect(
            self.endpoint,
            namespace=self.namespace_id,
            data_converter=pydantic_data_converter,
        )
        return client


class TemporalClientFactory:
    """
    Temporal client factory.
    """

    @staticmethod
    async def create_client() -> Client:
        """
        Create a Temporal client based on the environment.
        """
        environment = os.environ.get("environment", "dev")
        if environment == "dev":
            return await TemporalDevClient().connect()

        return await TemporalCloudClient(
            namespace="kawo-is-awesome-aws-use1",
            cert_path=Path(f"{CERT_DIR}/client.pem"),
            key_path=Path(f"{CERT_DIR}/client.key"),
        ).connect()
