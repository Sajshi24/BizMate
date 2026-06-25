import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.services import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Analytics"])


class SalesTrendPointResponse(BaseModel):
    date: str
    sales_count: int = Field(..., ge=0)


class RevenueTrendPointResponse(BaseModel):
    date: str
    revenue: float = Field(..., ge=0)


class TopProductResponse(BaseModel):
    product_id: str
    product_name: str
    quantity_sold: int = Field(..., ge=0)
    revenue: float = Field(..., ge=0)


class CategoryPerformanceResponse(BaseModel):
    category: str
    revenue: float = Field(..., ge=0)
    sales_count: int = Field(..., ge=0)


class AnalyticsSummaryResponse(BaseModel):
    total_revenue: float = Field(..., ge=0)
    total_profit: float
    total_sales: int = Field(..., ge=0)
    top_product: str | None = None
    best_category: str | None = None


@router.get(
    "/sales-trend",
    response_model=list[SalesTrendPointResponse],
    summary="Get daily sales count trend",
)
def get_sales_trend() -> list[SalesTrendPointResponse]:
    try:
        trend = analytics_service.get_sales_trend()
        return [
            SalesTrendPointResponse(date=point.date, sales_count=point.sales_count)
            for point in trend
        ]
    except PyMongoError as exc:
        logger.error("Database error while fetching sales trend: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/revenue-trend",
    response_model=list[RevenueTrendPointResponse],
    summary="Get daily revenue trend",
)
def get_revenue_trend() -> list[RevenueTrendPointResponse]:
    try:
        trend = analytics_service.get_revenue_trend()
        return [
            RevenueTrendPointResponse(date=point.date, revenue=point.revenue)
            for point in trend
        ]
    except PyMongoError as exc:
        logger.error("Database error while fetching revenue trend: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/top-products",
    response_model=list[TopProductResponse],
    summary="Get products ranked by quantity sold",
)
def get_top_products() -> list[TopProductResponse]:
    try:
        products = analytics_service.get_top_products()
        return [
            TopProductResponse(
                product_id=product.product_id,
                product_name=product.product_name,
                quantity_sold=product.quantity_sold,
                revenue=product.revenue,
            )
            for product in products
        ]
    except PyMongoError as exc:
        logger.error("Database error while fetching top products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/category-performance",
    response_model=list[CategoryPerformanceResponse],
    summary="Get revenue grouped by category",
)
def get_category_performance() -> list[CategoryPerformanceResponse]:
    try:
        categories = analytics_service.get_category_performance()
        return [
            CategoryPerformanceResponse(
                category=row.category,
                revenue=row.revenue,
                sales_count=row.sales_count,
            )
            for row in categories
        ]
    except PyMongoError as exc:
        logger.error("Database error while fetching category performance: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/summary",
    response_model=AnalyticsSummaryResponse,
    summary="Get analytics summary",
)
def get_analytics_summary() -> AnalyticsSummaryResponse:
    try:
        summary = analytics_service.get_analytics_summary()
        return AnalyticsSummaryResponse(
            total_revenue=summary.total_revenue,
            total_profit=summary.total_profit,
            total_sales=summary.total_sales,
            top_product=summary.top_product,
            best_category=summary.best_category,
        )
    except PyMongoError as exc:
        logger.error("Database error while fetching analytics summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc
