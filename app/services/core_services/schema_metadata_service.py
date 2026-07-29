"""Builds and ingests Order Processing schema metadata for RAG-based SQL generation."""

from typing import List

from langchain_core.documents import Document
from langchain_qdrant import QdrantVectorStore

from app.config.env_config import settings
from app.config.log_config import logger
from app.repository.vector_repository.qdrant_repository import qdrant_repository

# Human-readable table/column descriptions used as the RAG knowledge base.
# The LLM retrieves the relevant subset of this metadata before generating SQL.
SCHEMA_METADATA: List[dict] = [
    {
        "table": "customers",
        "description": (
            "Customers table stores customer details. Columns: "
            "customer_id (integer, primary key), "
            "customer_name (text, the customer's display name, e.g. 'John Smith' or 'ABC Ltd.'), "
            "email (text, customer email address)."
        ),
    },
    {
        "table": "orders",
        "description": (
            "Orders table stores order header information. Columns: "
            "order_id (integer, primary key), "
            "customer_id (integer, foreign key to customers.customer_id), "
            "order_date (timestamp, when the order was placed), "
            "status (text, one of 'Pending', 'Shipped', 'Delivered', 'Cancelled'), "
            "total_amount (numeric, total order value in USD). "
            "Join to customers via orders.customer_id = customers.customer_id."
        ),
    },
    {
        "table": "order_items",
        "description": (
            "OrderItems table stores products purchased in each order (line items). Columns: "
            "order_item_id (integer, primary key), "
            "order_id (integer, foreign key to orders.order_id), "
            "product_id (integer, foreign key to products.product_id), "
            "quantity (integer, units purchased), "
            "unit_price (numeric, price per unit at time of purchase). "
            "Join to orders via order_items.order_id = orders.order_id, "
            "and to products via order_items.product_id = products.product_id."
        ),
    },
    {
        "table": "products",
        "description": (
            "Products table is the product catalog. Columns: "
            "product_id (integer, primary key), "
            "product_name (text, e.g. 'Wireless Mouse'), "
            "category (text, e.g. 'Electronics', 'Furniture'), "
            "price (numeric, catalog price in USD)."
        ),
    },
    {
        "table": "shipments",
        "description": (
            "Shipments table stores shipment and delivery information, one row per order. Columns: "
            "shipment_id (integer, primary key), "
            "order_id (integer, foreign key to orders.order_id), "
            "carrier (text, e.g. 'FedEx', 'UPS', 'DHL'), "
            "tracking_number (text), "
            "delivery_status (text, one of 'Pending', 'In Transit', 'Delivered', 'Delayed'), "
            "shipped_date (timestamp, nullable), "
            "delivered_date (timestamp, nullable). "
            "Join to orders via shipments.order_id = orders.order_id."
        ),
    },
]


def get_schema_documents() -> List[Document]:
    """Build LangChain Documents from the schema metadata catalog.

    Returns:
        List of Document objects, one per table, tagged with table metadata.
    """
    return [
        Document(page_content=entry["description"], metadata={"table": entry["table"]})
        for entry in SCHEMA_METADATA
    ]


class SchemaMetadataService:
    """Ingests and retrieves Order Processing schema metadata via Qdrant."""

    def __init__(self) -> None:
        """Initialize with the dedicated schema-metadata collection name."""
        self.collection_name = settings.ORDER_SCHEMA_COLLECTION_NAME
        self.qdrant_repo = qdrant_repository

    def ingest_schema_metadata(self) -> QdrantVectorStore:
        """Embed and store schema metadata documents into Qdrant.

        Idempotent: re-running simply re-upserts the same documents.

        Returns:
            The Qdrant vector store the documents were written to.
        """
        vectordb = self.qdrant_repo.build_vectordb(collection_name=self.collection_name)
        documents = get_schema_documents()
        vectordb.add_documents(documents)
        logger.info(
            "Ingested %d schema metadata documents into collection=%s",
            len(documents),
            self.collection_name,
        )
        return vectordb

    # def retrieve_relevant_schema(self, query: str, k: int = 3) -> List[Document]:
    #     """Retrieve the schema documents most relevant to a natural language query.

    #     Args:
    #         query: User's natural language question.
    #         k: Number of top matching table descriptions to return.

    #     Returns:
    #         List of matching Document objects (empty list on failure).
    #     """
    #     try:
    #         vectordb = self.qdrant_repo.build_vectordb(
    #             collection_name=self.collection_name
    #         )
    #         return vectordb.similarity_search(query, k=k)
    #     except Exception as exc:
    #         logger.exception("Schema metadata retrieval failed: %s", exc)
    #         # Fall back to returning the full (small) metadata catalog so the
    #         # assistant can still attempt SQL generation.
    #         return get_schema_documents()
    def retrieve_relevant_schema(self, query: str, k: int = 3) -> List[Document]:
        """Retrieve the schema documents most relevant to a natural language query.

        Args:
            query: User's natural language question.
            k: Number of top matching table descriptions to return.

        Returns:
            List of matching Document objects. Falls back to the full schema
            catalog if Qdrant is unreachable OR if the collection returns no
            matches (e.g. it exists but schema metadata was never ingested).
        """
        try:
            vectordb = self.qdrant_repo.build_vectordb(
                collection_name=self.collection_name
            )
            results = vectordb.similarity_search(query, k=k)
        except Exception as exc:
            logger.exception("Schema metadata retrieval failed: %s", exc)
            return get_schema_documents()

        if not results:
            logger.warning(
                "Schema metadata collection '%s' returned no matches for "
                "query=%r. This usually means schema metadata was never "
                "ingested — run `python -m app.workers.order_bootstrap_worker`. "
                "Falling back to the full schema catalog.",
                self.collection_name,
                query,
            )
            return get_schema_documents()

        return results

schema_metadata_service = SchemaMetadataService()
