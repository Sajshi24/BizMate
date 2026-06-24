import logging

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.services import finance_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/finance", tags=["Finance"])


class FinanceSummaryResponse(BaseModel):
    total_revenue: float = Field(..., ge=0)
    total_cost: float = Field(..., ge=0)
    total_profit: float
    total_sales: int = Field(..., ge=0)


class RevenueResponse(BaseModel):
    total_revenue: float = Field(..., ge=0)


class ProfitResponse(BaseModel):
    total_profit: float
    profit_margin: float


class FinanceDashboardResponse(BaseModel):
    revenue: float = Field(..., ge=0)
    profit: float
    profit_margin: float
    total_sales: int = Field(..., ge=0)


@router.get(
    "/summary",
    response_model=FinanceSummaryResponse,
    summary="Get finance summary",
)
def get_finance_summary() -> FinanceSummaryResponse:
    try:
        metrics = finance_service.get_finance_summary()
        return FinanceSummaryResponse(
            total_revenue=metrics.total_revenue,
            total_cost=metrics.total_cost,
            total_profit=metrics.total_profit,
            total_sales=metrics.total_sales,
        )
    except PyMongoError as exc:
        logger.error("Database error while fetching finance summary: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/revenue",
    response_model=RevenueResponse,
    summary="Get total revenue",
)
def get_revenue() -> RevenueResponse:
    try:
        return RevenueResponse(total_revenue=finance_service.get_total_revenue())
    except PyMongoError as exc:
        logger.error("Database error while fetching revenue: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/profit",
    response_model=ProfitResponse,
    summary="Get total profit and margin",
)
def get_profit() -> ProfitResponse:
    try:
        metrics = finance_service.get_profit_metrics()
        return ProfitResponse(
            total_profit=metrics.total_profit,
            profit_margin=metrics.profit_margin,
        )
    except PyMongoError as exc:
        logger.error("Database error while fetching profit metrics: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/dashboard",
    response_model=FinanceDashboardResponse,
    summary="Get finance dashboard metrics",
)
def get_finance_dashboard() -> FinanceDashboardResponse:
    try:
        metrics = finance_service.get_finance_dashboard()
        return FinanceDashboardResponse(
            revenue=metrics.total_revenue,
            profit=metrics.total_profit,
            profit_margin=metrics.profit_margin,
            total_sales=metrics.total_sales,
        )
    except PyMongoError as exc:
        logger.error("Database error while fetching finance dashboard: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc
