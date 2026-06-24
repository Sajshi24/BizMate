import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.models.product_model import ProductResponse
from backend.services import inventory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


class RestockSuggestionResponse(BaseModel):
    product_name: str
    current_stock: int = Field(..., ge=0)
    minimum_stock: int = Field(..., ge=0)
    suggested_reorder_quantity: int = Field(..., ge=0)


class InventoryHealthResponse(BaseModel):
    total_products: int = Field(..., ge=0)
    healthy_products: int = Field(..., ge=0)
    low_stock_products: int = Field(..., ge=0)
    out_of_stock_products: int = Field(..., ge=0)
    health_score: float = Field(..., ge=0, le=100)


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="Get full inventory",
)
def get_inventory() -> list[ProductResponse]:
    try:
        return inventory_service.get_inventory()
    except PyMongoError as exc:
        logger.error("Database error while fetching inventory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/low-stock",
    response_model=list[ProductResponse],
    summary="Get low-stock products",
)
def get_low_stock_products() -> list[ProductResponse]:
    try:
        return inventory_service.get_low_stock_products()
    except PyMongoError as exc:
        logger.error("Database error while fetching low-stock products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/out-of-stock",
    response_model=list[ProductResponse],
    summary="Get out-of-stock products",
)
def get_out_of_stock_products() -> list[ProductResponse]:
    try:
        return inventory_service.get_out_of_stock_products()
    except PyMongoError as exc:
        logger.error("Database error while fetching out-of-stock products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/restock-suggestions",
    response_model=list[RestockSuggestionResponse],
    summary="Get restock suggestions",
)
def get_restock_suggestions() -> list[RestockSuggestionResponse]:
    try:
        suggestions = inventory_service.get_restock_suggestions()
        return [
            RestockSuggestionResponse(
                product_name=suggestion.product_name,
                current_stock=suggestion.current_stock,
                minimum_stock=suggestion.minimum_stock,
                suggested_reorder_quantity=suggestion.suggested_reorder_quantity,
            )
            for suggestion in suggestions
        ]
    except PyMongoError as exc:
        logger.error("Database error while fetching restock suggestions: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/health",
    response_model=InventoryHealthResponse,
    summary="Get inventory health metrics",
)
def get_inventory_health() -> InventoryHealthResponse:
    try:
        health = inventory_service.get_inventory_health()
        return InventoryHealthResponse(
            total_products=health.total_products,
            healthy_products=health.healthy_products,
            low_stock_products=health.low_stock_products,
            out_of_stock_products=health.out_of_stock_products,
            health_score=health.health_score,
        )
    except PyMongoError as exc:
        logger.error("Database error while fetching inventory health: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc
