import logging
from dataclasses import dataclass

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db

logger = logging.getLogger(__name__)

SALES_COLLECTION = "sales"


@dataclass
class FinanceMetrics:
    total_revenue: float
    total_cost: float
    total_profit: float
    total_sales: int
    profit_margin: float


def _get_collection() -> Collection:
    return db[SALES_COLLECTION]


def _calculate_profit_margin(total_profit: float, total_revenue: float) -> float:
    if total_revenue <= 0:
        return 0.0
    return round((total_profit / total_revenue) * 100, 2)


def _aggregate_finance_metrics() -> FinanceMetrics:
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "total_cost": {"$sum": "$cost"},
                "total_profit": {"$sum": "$profit"},
                "total_sales": {"$sum": 1},
            }
        }
    ]

    try:
        results = list(_get_collection().aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Failed to aggregate finance metrics: %s", exc)
        raise

    if not results:
        return FinanceMetrics(
            total_revenue=0.0,
            total_cost=0.0,
            total_profit=0.0,
            total_sales=0,
            profit_margin=0.0,
        )

    metrics = results[0]
    total_revenue = float(metrics["total_revenue"])
    total_profit = float(metrics["total_profit"])

    return FinanceMetrics(
        total_revenue=total_revenue,
        total_cost=float(metrics["total_cost"]),
        total_profit=total_profit,
        total_sales=int(metrics["total_sales"]),
        profit_margin=_calculate_profit_margin(total_profit, total_revenue),
    )


def get_finance_summary() -> FinanceMetrics:
    return _aggregate_finance_metrics()


def get_total_revenue() -> float:
    return _aggregate_finance_metrics().total_revenue


def get_profit_metrics() -> FinanceMetrics:
    return _aggregate_finance_metrics()


def get_finance_dashboard() -> FinanceMetrics:
    return _aggregate_finance_metrics()
