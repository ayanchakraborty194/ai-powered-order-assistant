"""One-off bootstrap for the Order Processing PoC.

Run with: python -m app.workers.order_bootstrap_worker

Creates the Postgres schema, seeds sample data, and ingests the schema
metadata knowledge base into Qdrant for RAG-based SQL generation.
"""

from app.config.env_config import settings
from app.config.log_config import logger
from app.services.core_services.schema_metadata_service import (
    schema_metadata_service,
)
from app.utils.core_utils.order_db_seed import create_order_db_schema, seed_sample_data


def main() -> None:
    """Run the full bootstrap sequence."""
    if not settings.USE_ORDER_DB:
        logger.info("USE_ORDER_DB is false. Skipping order DB bootstrap.")
        return

    logger.info("Creating order processing schema...")
    create_order_db_schema()

    logger.info("Seeding sample data...")
    seed_sample_data()

    if settings.USE_QDRANT:
        logger.info("Ingesting schema metadata into Qdrant...")
        schema_metadata_service.ingest_schema_metadata()
    else:
        logger.info("USE_QDRANT is false. Skipping schema metadata ingestion.")

    logger.info("Order processing bootstrap complete.")


if __name__ == "__main__":
    main()
