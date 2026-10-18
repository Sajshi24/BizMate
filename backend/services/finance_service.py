import logging
from dataclasses import dataclass

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db

logger = logging.getLogger(__name__)

SALES_COLLECTION = "sales"
PRODUCTS_COLLECTION = "products"


@dataclass
class FinanceMetrics:
    total_revenue: float
    total_cost: float
    total_profit: float
    total_sales: int
    profit_margin: float


@dataclass
class ExpenseItem:
    name: str
    value: float


@dataclass
class MonthlySummaryItem:
    month: str
    label: str
    revenue: float
    expenses: float
    profit: float


def _get_collection() -> Collection:
    return db[SALES_COLLECTION]


def _calculate_profit_margin(total_profit: float, total_revenue: float) -> float:
    if total_revenue <= 0:
        return 0.0
    return round((total_profit / total_revenue) * 100, 2)


def _aggregate_finance_metrics(user_id: str) -> FinanceMetrics:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "total_cost": {"$sum": "$cost"},
                "total_profit": {"$sum": "$profit"},
                "total_sales": {"$sum": 1},
            }
        },
    ]

    try:
        results = list(_get_collection().aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Failed to aggregate finance metrics for user %s: %s", user_id, exc)
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


def get_finance_summary(user_id: str) -> FinanceMetrics:
    return _aggregate_finance_metrics(user_id)


def get_total_revenue(user_id: str) -> float:
    return _aggregate_finance_metrics(user_id).total_revenue


def get_profit_metrics(user_id: str) -> FinanceMetrics:
    return _aggregate_finance_metrics(user_id)


def get_finance_dashboard(user_id: str) -> FinanceMetrics:
    return _aggregate_finance_metrics(user_id)


def get_expense_breakdown(user_id: str) -> list[ExpenseItem]:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$lookup": {
                "from": PRODUCTS_COLLECTION,
                "let": {"pid": "$product_id", "uid": "$user_id"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$eq": ["$product_id", "$$pid"]},
                                    {"$eq": ["$user_id", "$$uid"]},
                                ]
                            }
                        }
                    }
                ],
                "as": "product",
            }
        },
        {
            "$unwind": {
                "path": "$product",
                "preserveNullAndEmptyArrays": True,
            }
        },
        {
            "$group": {
                "_id": {
                    "$ifNull": [
                        "$product.category",
                        {"$ifNull": ["$category", "Inventory & Stock"]},
                    ]
                },
                "total_cost": {"$sum": "$cost"},
            }
        },
        {"$sort": {"total_cost": -1}},
    ]
    try:
        results = list(_get_collection().aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Failed to get expense breakdown for user %s: %s", user_id, exc)
        raise

    items = []
    for r in results:
        cost = float(r.get("total_cost", 0.0))
        if cost > 0:
            cat_name = r.get("_id") or "General Inventory"
            items.append(ExpenseItem(name=f"{cat_name} Cost", value=round(cost, 2)))
    return items


def get_monthly_summary(user_id: str) -> list[MonthlySummaryItem]:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    curr_year = now.year
    curr_month = now.month
    months = []
    for i in range(11, -1, -1):
        m = curr_month - i
        y = curr_year
        while m <= 0:
            m += 12
            y -= 1
        months.append((y, m))

    start_date = datetime(months[0][0], months[0][1], 1, tzinfo=timezone.utc)
    pipeline = [
        {"$match": {"user_id": user_id, "sale_date": {"$gte": start_date}}},
        {
            "$group": {
                "_id": {"$dateToString": {"format": "%Y-%m", "date": "$sale_date"}},
                "revenue": {"$sum": "$revenue"},
                "expenses": {"$sum": "$cost"},
                "profit": {"$sum": "$profit"},
            }
        },
    ]
    try:
        results = {row["_id"]: row for row in _get_collection().aggregate(pipeline)}
    except PyMongoError as exc:
        logger.error("Failed to get monthly summary for user %s: %s", user_id, exc)
        raise

    month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    summary = []
    for y, m in months:
        m_str = f"{y:04d}-{m:02d}"
        row = results.get(m_str, {})
        rev = float(row.get("revenue", 0.0))
        exp = float(row.get("expenses", 0.0))
        prof = float(row.get("profit", 0.0))
        summary.append(
            MonthlySummaryItem(
                month=m_str,
                label=f"{month_names[m]} {y}",
                revenue=rev,
                expenses=exp,
                profit=prof,
            )
        )
    return summary
