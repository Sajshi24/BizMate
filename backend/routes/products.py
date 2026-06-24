import logging

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from backend.models.product_model import (
    ProductCreate,
    ProductDeleteResponse,
    ProductResponse,
    ProductUpdate,
)
from backend.services import product_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(payload: ProductCreate) -> ProductResponse:
    try:
        return product_service.create_product(payload)
    except PyMongoError as exc:
        logger.error("Database error while creating product: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List all products",
)
def list_products() -> list[ProductResponse]:
    try:
        return product_service.get_all_products()
    except PyMongoError as exc:
        logger.error("Database error while listing products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
)
def get_product(product_id: str) -> ProductResponse:
    try:
        return product_service.get_product_by_id(product_id)
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error while fetching product %s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
)
def update_product(product_id: str, payload: ProductUpdate) -> ProductResponse:
    try:
        return product_service.update_product(product_id, payload)
    except product_service.ProductValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error while updating product %s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
    summary="Delete a product",
)
def delete_product(product_id: str) -> ProductDeleteResponse:
    try:
        deleted_id = product_service.delete_product(product_id)
        return ProductDeleteResponse(
            message="Product deleted successfully",
            product_id=deleted_id,
        )
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error while deleting product %s: %s", product_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc
