import logging
from datetime import UTC, datetime
from uuid import uuid4

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db
from backend.models.sale_model import SaleCreate, SaleResponse

logger = logging.getLogger(__name__)

SALES_COLLECTION = "sales"
PRODUCTS_COLLECTION = "products"


class SaleNotFoundError(Exception):
    """Raised when a sale does not exist."""


class ProductNotFoundError(Exception):
    """Raised when a referenced product does not exist."""


class InsufficientStockError(Exception):
    """Raised when product stock is too low for the requested sale."""


def _get_sales_collection() -> Collection:
    return db[SALES_COLLECTION]


def _get_products_collection() -> Collection:
    return db[PRODUCTS_COLLECTION]


def create_sale(payload: SaleCreate) -> SaleResponse:
    try:
        product = _get_products_collection().find_one_and_update(
            {
                "product_id": payload.product_id,
                "stock": {"$gte": payload.quantity},
            },
            {"$inc": {"stock": -payload.quantity}},
            return_document=ReturnDocument.BEFORE,
            projection={"_id": 0},
        )
    except PyMongoError as exc:
        logger.error("Failed to process sale for product %s: %s", payload.product_id, exc)
        raise

    if product is None:
        try:
            exists = _get_products_collection().find_one(
                {"product_id": payload.product_id},
                {"_id": 1},
            )
        except PyMongoError as exc:
            logger.error("Failed to verify product %s: %s", payload.product_id, exc)
            raise

        if exists is None:
            raise ProductNotFoundError(f"Product '{payload.product_id}' not found")

        raise InsufficientStockError(
            f"Insufficient stock for product '{payload.product_id}'"
        )

    unit_cost = product["cost_price"]
    unit_price = product["selling_price"]
    revenue = payload.quantity * unit_price
    cost = payload.quantity * unit_cost
    profit = revenue - cost

    sale_id = str(uuid4())
    document = {
        "sale_id": sale_id,
        "product_id": payload.product_id,
        "product_name": product["name"],
        "quantity": payload.quantity,
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "revenue": revenue,
        "cost": cost,
        "profit": profit,
        "sale_date": datetime.now(UTC),
    }

    try:
        _get_sales_collection().insert_one(document)
        logger.info("Created sale %s for product %s", sale_id, payload.product_id)
    except PyMongoError as exc:
        logger.error("Failed to save sale for product %s: %s", payload.product_id, exc)
        try:
            _get_products_collection().update_one(
                {"product_id": payload.product_id},
                {"$inc": {"stock": payload.quantity}},
            )
        except PyMongoError as rollback_exc:
            logger.error(
                "Failed to rollback stock for product %s: %s",
                payload.product_id,
                rollback_exc,
            )
        raise

    return SaleResponse(**document)


def get_all_sales() -> list[SaleResponse]:
    try:
        documents = list(_get_sales_collection().find({}, {"_id": 0}))
    except PyMongoError as exc:
        logger.error("Failed to fetch sales: %s", exc)
        raise

    return [SaleResponse(**document) for document in documents]


def get_sale_by_id(sale_id: str) -> SaleResponse:
    try:
        document = _get_sales_collection().find_one({"sale_id": sale_id}, {"_id": 0})
    except PyMongoError as exc:
        logger.error("Failed to fetch sale %s: %s", sale_id, exc)
        raise

    if document is None:
        raise SaleNotFoundError(f"Sale '{sale_id}' not found")

    return SaleResponse(**document)
