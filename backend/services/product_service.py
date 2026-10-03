import logging
from datetime import UTC, datetime
from uuid import uuid4

from pymongo import ReturnDocument
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db
from backend.models.product_model import ProductCreate, ProductResponse, ProductUpdate

logger = logging.getLogger(__name__)

COLLECTION_NAME = "products"


class ProductNotFoundError(Exception):
    """Raised when a product does not exist or does not belong to the user."""


class ProductValidationError(Exception):
    """Raised when update payload contains no fields."""


def _get_collection() -> Collection:
    return db[COLLECTION_NAME]


def create_product(payload: ProductCreate, user_id: str) -> ProductResponse:
    product_id = str(uuid4())
    data = payload.model_dump(exclude={"user_id"})
    document = {
        "product_id": product_id,
        "user_id": user_id,
        **data,
        "created_at": datetime.now(UTC),
    }

    try:
        _get_collection().insert_one(document)
        logger.info("Created product %s for user %s", product_id, user_id)
    except PyMongoError as exc:
        logger.error("Failed to create product for user %s: %s", user_id, exc)
        raise

    return ProductResponse(**document)


def get_all_products(user_id: str) -> list[ProductResponse]:
    try:
        documents = list(_get_collection().find({"user_id": user_id}, {"_id": 0}))
    except PyMongoError as exc:
        logger.error("Failed to fetch products for user %s: %s", user_id, exc)
        raise

    return [ProductResponse(**document) for document in documents]


def get_product_by_id(product_id: str, user_id: str) -> ProductResponse:
    try:
        document = _get_collection().find_one(
            {"product_id": product_id, "user_id": user_id},
            {"_id": 0},
        )
    except PyMongoError as exc:
        logger.error("Failed to fetch product %s for user %s: %s", product_id, user_id, exc)
        raise

    if document is None:
        raise ProductNotFoundError(f"Product '{product_id}' not found")

    return ProductResponse(**document)


def update_product(product_id: str, payload: ProductUpdate, user_id: str) -> ProductResponse:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise ProductValidationError("At least one field must be provided for update")

    # Don't allow modifying user_id
    updates.pop("user_id", None)

    try:
        result = _get_collection().find_one_and_update(
            {"product_id": product_id, "user_id": user_id},
            {"$set": updates},
            return_document=ReturnDocument.AFTER,
            projection={"_id": 0},
        )
    except PyMongoError as exc:
        logger.error("Failed to update product %s for user %s: %s", product_id, user_id, exc)
        raise

    if result is None:
        raise ProductNotFoundError(f"Product '{product_id}' not found")

    logger.info("Updated product %s for user %s", product_id, user_id)
    return ProductResponse(**result)


def delete_product(product_id: str, user_id: str) -> str:
    try:
        result = _get_collection().delete_one({"product_id": product_id, "user_id": user_id})
    except PyMongoError as exc:
        logger.error("Failed to delete product %s for user %s: %s", product_id, user_id, exc)
        raise

    if result.deleted_count == 0:
        raise ProductNotFoundError(f"Product '{product_id}' not found")

    logger.info("Deleted product %s for user %s", product_id, user_id)
    return product_id
