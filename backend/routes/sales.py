import logging

from fastapi import APIRouter, HTTPException, status
from pymongo.errors import PyMongoError

from backend.models.sale_model import SaleCreate, SaleResponse
from backend.services import sales_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sales", tags=["Sales"])


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a sale",
)
def create_sale(payload: SaleCreate) -> SaleResponse:
    try:
        return sales_service.create_sale(payload)
    except sales_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except sales_service.InsufficientStockError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error while creating sale: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "",
    response_model=list[SaleResponse],
    summary="List all sales",
)
def list_sales() -> list[SaleResponse]:
    try:
        return sales_service.get_all_sales()
    except PyMongoError as exc:
        logger.error("Database error while listing sales: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get a sale by ID",
)
def get_sale(sale_id: str) -> SaleResponse:
    try:
        return sales_service.get_sale_by_id(sale_id)
    except sales_service.SaleNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error("Database error while fetching sale %s: %s", sale_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc
