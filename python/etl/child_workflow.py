"""
Daily Sales Report ETL Pipeline.

To run this Workflow:

1. Start Temporal development server in a terminal.

    ```bash
    temporal server start-dev
    ```

2. In a new terminal, run the workflow:

    ```bash
    uv run poe etl_child_workflow
    ```

Supports Temporal Cloud via environment variables:

    TEMPORAL_ADDRESS    Server address  (default: localhost:7233)
    TEMPORAL_NAMESPACE  Namespace       (default: default)
    TEMPORAL_API_KEY    API key — when set, enables TLS and targets Temporal Cloud
"""

import asyncio
import logging
import os
import random
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.exceptions import ApplicationError
from temporalio.worker import Worker

TASK_QUEUE = "daily-sales-report-task-queue"


@dataclass
class Order:
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    unit_price: float


@dataclass
class EnrichedOrder:
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    unit_price: float
    discounted_unit_price: float
    total: float


@dataclass
class Product:
    product_id: str
    name: str
    category: str
    discount_rate: float


@dataclass
class OrderTotal:
    order_id: str
    customer_id: str
    product_id: str
    quantity: int
    total: float


@dataclass
class SalesReport:
    date: str
    total_orders: int
    total_revenue: float
    revenue_by_category: dict[str, float] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Workflow Input / Output Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class ExtractInput:
    date: str


@dataclass
class CatalogInput:
    date: str


@dataclass
class AggregateInput:
    date: str
    totals_key: str  # claim-check key produced by CW2
    catalog_key: str  # claim-check key produced by CW3


# ---------------------------------------------------------------------------
# Mock Source Data
# ---------------------------------------------------------------------------

_MOCK_ORDERS: list[Order] = [
    Order("ORD-001", "C-101", "P-A", 2, 49.99),
    Order("ORD-002", "C-102", "P-B", 1, 129.99),
    Order("ORD-003", "C-101", "P-C", 3, 19.99),
    Order("ORD-004", "C-103", "P-A", 1, 49.99),
    Order("ORD-005", "C-102", "P-D", 2, 89.99),
]

_MOCK_CATALOG: list[Product] = [
    Product("P-A", "Wireless Headphones", "Electronics", 0.10),
    Product("P-B", "Mechanical Keyboard", "Electronics", 0.05),
    Product("P-C", "USB-C Cable", "Accessories", 0.15),
    Product("P-D", "Laptop Stand", "Accessories", 0.10),
]


# ---------------------------------------------------------------------------
# Activities — ETL Orders
# ---------------------------------------------------------------------------


@activity.defn
def load_orders(input: ExtractInput) -> str:
    """Load raw orders for the given date."""
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Loading orders for date=%s", input.date)
    key = f"s3://orders/{input.date}.parquet"
    activity.logger.info("Storing orders in %s", key)
    return key


@activity.defn
def validate_orders(raw_orders_key: str) -> bool:
    """Validate raw orders (drop any with non-positive qty or price)."""
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Validating orders from %s", raw_orders_key)
    return True


@activity.defn
def compute_order_totals(raw_order_s3_key: str) -> str:
    """Flatten enriched orders into a lightweight OrderTotal list."""
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Loading orders from %s", raw_order_s3_key)
    activity.logger.info("Computing order totals...")
    new_key = f"s3://order_totals/{raw_order_s3_key.split('/')[-1]}"
    activity.logger.info("Storing order totals in %s", new_key)
    return new_key


# ---------------------------------------------------------------------------
# Activities — ETL Product Catalog
# ---------------------------------------------------------------------------


@activity.defn
def load_product_catalog(input: CatalogInput) -> str:
    """Fetch the full product catalog for the given date."""
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Loading product catalog for date=%s", input.date)
    s3_key = f"s3://product_catalog/{input.date}.parquet"
    activity.logger.info("Storing product catalog in %s", s3_key)
    return s3_key


@activity.defn
def index_product_catalog(raw_catalog_key: str) -> str:
    """Build a product_id → Product index for O(1) lookups during aggregation."""
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Loading product catalog from %s", raw_catalog_key)
    activity.logger.info("Indexing product catalog...")
    new_key = f"s3://indexed_product_catalog/{raw_catalog_key.split('/')[-1]}"
    activity.logger.info("Storing indexed product catalog in %s", new_key)
    return new_key


# ---------------------------------------------------------------------------
# Activities — Parent: Aggregation
# ---------------------------------------------------------------------------


@activity.defn
def generate_sales_report(input: AggregateInput) -> str:
    """
    Join order totals with the product catalog and produce the sales report.

    Loads both claim-check payloads, enriches each order with its product
    category, and aggregates revenue by category.
    """
    time.sleep(random.uniform(1, 2))
    activity.logger.info("Loading order totals from %s", input.totals_key)
    activity.logger.info("Loading product catalog from %s", input.catalog_key)
    activity.logger.info("Generating sales report...")
    activity.logger.info("Joining order totals with product catalog...")
    activity.logger.info("Aggregating revenue by category...")
    activity.logger.info("Generating sales report...")
    new_key = f"s3://sales_report/{input.date}.parquet"
    activity.logger.info("Storing sales report in %s", new_key)
    return new_key


@workflow.defn
class EtlOrdersWorkflow:
    """
    CW1: Fetch and validate raw orders.

    Returns the claim-check key for the validated orders list.
    """

    @workflow.run
    async def run(self, input: ExtractInput) -> str:
        raw_order_s3_key = await workflow.execute_activity(
            load_orders,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )
        is_order_dataset_valid = await workflow.execute_activity(
            validate_orders,
            raw_order_s3_key,
            start_to_close_timeout=timedelta(seconds=10),
        )
        if not is_order_dataset_valid:
            raise ApplicationError("Invalid orders dataset. Failing Workflow.")

        order_total_s3_key = await workflow.execute_activity(
            compute_order_totals,
            raw_order_s3_key,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return order_total_s3_key


@workflow.defn
class EtlProductCatalogWorkflow:
    """
    CW3: Fetch and index the product catalog.

    Runs in parallel with CW1 — has no dependency on order data.
    Returns the claim-check key for the indexed catalog dict.
    """

    @workflow.run
    async def run(self, input: CatalogInput) -> str:
        raw_catalog_key = await workflow.execute_activity(
            load_product_catalog,
            input,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return await workflow.execute_activity(
            index_product_catalog,
            raw_catalog_key,
            start_to_close_timeout=timedelta(seconds=10),
        )


@workflow.defn
class DailySalesReportWorkflow:
    @workflow.run
    async def run(self, date: str) -> str:
        workflow.logger.info("Starting ETL pipeline for date=%s", date)

        # ── Step 1: CW1 and CW3 start in parallel ──────────────────────────
        order_handle = await workflow.start_child_workflow(
            EtlOrdersWorkflow.run,
            ExtractInput(date=date),
            id=f"etl-orders-{date}",
            task_queue=TASK_QUEUE,
        )
        catalog_handle = await workflow.start_child_workflow(
            EtlProductCatalogWorkflow.run,
            CatalogInput(date=date),
            id=f"etl-product-catalog-{date}",
            task_queue=TASK_QUEUE,
        )

        transformed_order_key, transformed_catalog_key = await asyncio.gather(
            order_handle,
            catalog_handle,
        )

        return await workflow.execute_activity(
            generate_sales_report,
            AggregateInput(
                date=date,
                totals_key=transformed_order_key,
                catalog_key=transformed_catalog_key,
            ),
            start_to_close_timeout=timedelta(seconds=10),
        )


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

    client = await connect_client()

    async with Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[
            DailySalesReportWorkflow,
            EtlOrdersWorkflow,
            EtlProductCatalogWorkflow,
        ],
        activities=[
            load_orders,
            validate_orders,
            compute_order_totals,
            load_product_catalog,
            index_product_catalog,
            generate_sales_report,
        ],
        activity_executor=ThreadPoolExecutor(10),
    ):
        report_s3_key = await client.execute_workflow(
            DailySalesReportWorkflow.run,
            "2026-04-26",
            id=f"daily-sales-report-{uuid.uuid4()}",
            task_queue=TASK_QUEUE,
        )

        print(f"Sales report stored in {report_s3_key}")


if __name__ == "__main__":
    asyncio.run(main())
