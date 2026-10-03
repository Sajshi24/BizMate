import logging

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from pymongo.errors import PyMongoError

from backend.models.user_model import UserResponse
from backend.routes.deps import get_current_user
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
    summary="Get finance summary for the authenticated user",
)
def get_finance_summary(
    current_user: UserResponse = Depends(get_current_user),
) -> FinanceSummaryResponse:
    try:
        metrics = finance_service.get_finance_summary(current_user.user_id)
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
    summary="Get total revenue for the authenticated user",
)
def get_revenue(
    current_user: UserResponse = Depends(get_current_user),
) -> RevenueResponse:
    try:
        return RevenueResponse(total_revenue=finance_service.get_total_revenue(current_user.user_id))
    except PyMongoError as exc:
        logger.error("Database error while fetching revenue: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "/profit",
    response_model=ProfitResponse,
    summary="Get total profit and margin for the authenticated user",
)
def get_profit(
    current_user: UserResponse = Depends(get_current_user),
) -> ProfitResponse:
    try:
        metrics = finance_service.get_profit_metrics(current_user.user_id)
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
    summary="Get finance dashboard metrics for the authenticated user",
)
def get_finance_dashboard(
    current_user: UserResponse = Depends(get_current_user),
) -> FinanceDashboardResponse:
    try:
        metrics = finance_service.get_finance_dashboard(current_user.user_id)
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
