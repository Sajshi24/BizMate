import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from pymongo.errors import PyMongoError

from backend.services import analytics_service, finance_service, gemini_service, inventory_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/advisor", tags=["AI Advisor"])


class AdviceResponse(BaseModel):
    advice: str


@router.get(
    "/advice",
    response_model=AdviceResponse,
    summary="Get AI-powered business advice from live data",
)
def get_business_advice() -> AdviceResponse:
    try:
        finance = finance_service.get_finance_summary()
        analytics = analytics_service.get_analytics_summary()
        inventory = inventory_service.get_inventory_health()
    except PyMongoError as exc:
        logger.error("Database error while collecting business context: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc

    business_data: dict[str, Any] = {
        "total_revenue": finance.total_revenue,
        "total_profit": finance.total_profit,
        "profit_margin_percent": finance.profit_margin,
        "total_sales": finance.total_sales,
        "top_selling_product": analytics.top_product,
        "best_revenue_category": analytics.best_category,
        "inventory_health_score": inventory.health_score,
        "low_stock_product_count": inventory.low_stock_products,
        "out_of_stock_product_count": inventory.out_of_stock_products,
        "total_products": inventory.total_products,
    }

    result = gemini_service.generate_business_advice(business_data)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=result.error or "AI advice generation failed.",
        )

    return AdviceResponse(advice=result.content)
