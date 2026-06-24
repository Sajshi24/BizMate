import logging
from dataclasses import dataclass

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db
from backend.models.product_model import ProductResponse

logger = logging.getLogger(__name__)

COLLECTION_NAME = "products"


@dataclass
class RestockSuggestion:
    product_name: str
    current_stock: int
    minimum_stock: int
    suggested_reorder_quantity: int


@dataclass
class InventoryHealth:
    total_products: int
    healthy_products: int
    low_stock_products: int
    out_of_stock_products: int
    health_score: float


def _get_collection() -> Collection:
    return db[COLLECTION_NAME]


def _documents_to_products(documents: list[dict]) -> list[ProductResponse]:
    return [ProductResponse(**document) for document in documents]


def _calculate_reorder_quantity(stock: int, minimum_stock: int) -> int:
    """Suggest enough units to reach double the minimum stock level."""
    return max((minimum_stock * 2) - stock, minimum_stock)


def get_inventory() -> list[ProductResponse]:
    try:
        documents = list(_get_collection().find({}, {"_id": 0}))
    except PyMongoError as exc:
        logger.error("Failed to fetch inventory: %s", exc)
        raise

    return _documents_to_products(documents)


def get_low_stock_products() -> list[ProductResponse]:
    try:
        documents = list(
            _get_collection().find(
                {"$expr": {"$lte": ["$stock", "$minimum_stock"]}},
                {"_id": 0},
            )
        )
    except PyMongoError as exc:
        logger.error("Failed to fetch low-stock products: %s", exc)
        raise

    return _documents_to_products(documents)


def get_out_of_stock_products() -> list[ProductResponse]:
    try:
        documents = list(_get_collection().find({"stock": 0}, {"_id": 0}))
    except PyMongoError as exc:
        logger.error("Failed to fetch out-of-stock products: %s", exc)
        raise

    return _documents_to_products(documents)


def get_restock_suggestions() -> list[RestockSuggestion]:
    try:
        documents = list(
            _get_collection().find(
                {"$expr": {"$lte": ["$stock", "$minimum_stock"]}},
                {"_id": 0, "name": 1, "stock": 1, "minimum_stock": 1},
            )
        )
    except PyMongoError as exc:
        logger.error("Failed to fetch restock suggestions: %s", exc)
        raise

    return [
        RestockSuggestion(
            product_name=document["name"],
            current_stock=document["stock"],
            minimum_stock=document["minimum_stock"],
            suggested_reorder_quantity=_calculate_reorder_quantity(
                document["stock"],
                document["minimum_stock"],
            ),
        )
        for document in documents
    ]


def get_inventory_health() -> InventoryHealth:
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_products": {"$sum": 1},
                "out_of_stock_products": {
                    "$sum": {"$cond": [{"$eq": ["$stock", 0]}, 1, 0]}
                },
                "low_stock_products": {
                    "$sum": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$gt": ["$stock", 0]},
                                    {"$lte": ["$stock", "$minimum_stock"]},
                                ]
                            },
                            1,
                            0,
                        ]
                    }
                },
                "healthy_products": {
                    "$sum": {
                        "$cond": [{"$gt": ["$stock", "$minimum_stock"]}, 1, 0]
                    }
                },
            }
        }
    ]

    try:
        results = list(_get_collection().aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Failed to calculate inventory health: %s", exc)
        raise

    if not results:
        return InventoryHealth(
            total_products=0,
            healthy_products=0,
            low_stock_products=0,
            out_of_stock_products=0,
            health_score=100.0,
        )

    metrics = results[0]
    total_products = metrics["total_products"]
    healthy_products = metrics["healthy_products"]
    health_score = (
        round((healthy_products / total_products) * 100, 2)
        if total_products > 0
        else 100.0
    )

    return InventoryHealth(
        total_products=total_products,
        healthy_products=healthy_products,
        low_stock_products=metrics["low_stock_products"],
        out_of_stock_products=metrics["out_of_stock_products"],
        health_score=health_score,
    )
