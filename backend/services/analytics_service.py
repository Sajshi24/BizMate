import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from backend.config.database import db

logger = logging.getLogger(__name__)

SALES_COLLECTION = "sales"
PRODUCTS_COLLECTION = "products"


@dataclass
class SalesTrendPoint:
    date: str
    sales_count: int


@dataclass
class RevenueTrendPoint:
    date: str
    revenue: float


@dataclass
class TrendPoint:
    label: str
    date: str
    revenue: float
    sales: int
    cost: float = 0.0
    profit: float = 0.0


@dataclass
class TopProduct:
    product_id: str
    product_name: str
    quantity_sold: int
    revenue: float


@dataclass
class CategoryPerformance:
    category: str
    revenue: float
    sales_count: int


@dataclass
class AnalyticsSummary:
    total_revenue: float
    total_profit: float
    total_sales: int
    top_product: str | None
    best_category: str | None
    average_order_value: float = 0.0
    repeat_customers_pct: float = 0.0



def _get_sales_collection() -> Collection:
    return db[SALES_COLLECTION]


def _run_aggregation(collection: Collection, pipeline: list) -> list:
    try:
        return list(collection.aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Analytics aggregation failed: %s", exc)
        raise


def get_sales_trend(user_id: str) -> list[SalesTrendPoint]:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$sale_date"}
                },
                "sales_count": {"$sum": 1},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "sales_count": 1,
            }
        },
    ]

    results = _run_aggregation(_get_sales_collection(), pipeline)
    return [
        SalesTrendPoint(date=row["date"], sales_count=int(row["sales_count"]))
        for row in results
    ]


def get_revenue_trend(user_id: str) -> list[RevenueTrendPoint]:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": {
                    "$dateToString": {"format": "%Y-%m-%d", "date": "$sale_date"}
                },
                "revenue": {"$sum": "$revenue"},
            }
        },
        {"$sort": {"_id": 1}},
        {
            "$project": {
                "_id": 0,
                "date": "$_id",
                "revenue": 1,
            }
        },
    ]

    results = _run_aggregation(_get_sales_collection(), pipeline)
    return [
        RevenueTrendPoint(date=row["date"], revenue=float(row["revenue"]))
        for row in results
    ]


def get_trend(user_id: str, range_type: str = "7d") -> list[TrendPoint]:
    now = datetime.now(timezone.utc)
    collection = _get_sales_collection()

    if range_type == "7d":
        days = []
        for i in range(6, -1, -1):
            d = (now - timedelta(days=i)).date()
            days.append(d)
        start_date = datetime.combine(days[0], datetime.min.time(), tzinfo=timezone.utc)

        pipeline = [
            {"$match": {"user_id": user_id, "sale_date": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$sale_date"}},
                    "revenue": {"$sum": "$revenue"},
                    "cost": {"$sum": "$cost"},
                    "profit": {"$sum": "$profit"},
                    "sales": {"$sum": 1},
                }
            },
        ]
        results = {row["_id"]: row for row in _run_aggregation(collection, pipeline)}
        points = []
        for d in days:
            d_str = d.strftime("%Y-%m-%d")
            row = results.get(d_str, {})
            points.append(
                TrendPoint(
                    label=d.strftime("%a"),
                    date=d_str,
                    revenue=float(row.get("revenue", 0.0)),
                    sales=int(row.get("sales", 0)),
                    cost=float(row.get("cost", 0.0)),
                    profit=float(row.get("profit", 0.0)),
                )
            )
        return points

    elif range_type == "30d":
        days = []
        for i in range(29, -1, -1):
            d = (now - timedelta(days=i)).date()
            days.append(d)
        start_date = datetime.combine(days[0], datetime.min.time(), tzinfo=timezone.utc)

        pipeline = [
            {"$match": {"user_id": user_id, "sale_date": {"$gte": start_date}}},
            {
                "$group": {
                    "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$sale_date"}},
                    "revenue": {"$sum": "$revenue"},
                    "cost": {"$sum": "$cost"},
                    "profit": {"$sum": "$profit"},
                    "sales": {"$sum": 1},
                }
            },
        ]
        results = {row["_id"]: row for row in _run_aggregation(collection, pipeline)}
        points = []
        for d in days:
            d_str = d.strftime("%Y-%m-%d")
            row = results.get(d_str, {})
            points.append(
                TrendPoint(
                    label=str(d.day),
                    date=d_str,
                    revenue=float(row.get("revenue", 0.0)),
                    sales=int(row.get("sales", 0)),
                    cost=float(row.get("cost", 0.0)),
                    profit=float(row.get("profit", 0.0)),
                )
            )
        return points

    elif range_type == "12m":
        months = []
        curr_year = now.year
        curr_month = now.month
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
                    "cost": {"$sum": "$cost"},
                    "profit": {"$sum": "$profit"},
                    "sales": {"$sum": 1},
                }
            },
        ]
        results = {row["_id"]: row for row in _run_aggregation(collection, pipeline)}
        points = []
        month_names = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        for y, m in months:
            m_str = f"{y:04d}-{m:02d}"
            row = results.get(m_str, {})
            points.append(
                TrendPoint(
                    label=month_names[m],
                    date=m_str,
                    revenue=float(row.get("revenue", 0.0)),
                    sales=int(row.get("sales", 0)),
                    cost=float(row.get("cost", 0.0)),
                    profit=float(row.get("profit", 0.0)),
                )
            )
        return points

    return []


def get_top_products(user_id: str) -> list[TopProduct]:
    pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": {
                    "product_id": "$product_id",
                    "product_name": "$product_name",
                },
                "quantity_sold": {"$sum": "$quantity"},
                "revenue": {"$sum": "$revenue"},
            }
        },
        {"$sort": {"quantity_sold": -1}},
        {
            "$project": {
                "_id": 0,
                "product_id": "$_id.product_id",
                "product_name": "$_id.product_name",
                "quantity_sold": 1,
                "revenue": 1,
            }
        },
    ]

    results = _run_aggregation(_get_sales_collection(), pipeline)
    return [
        TopProduct(
            product_id=row["product_id"],
            product_name=row["product_name"],
            quantity_sold=int(row["quantity_sold"]),
            revenue=float(row["revenue"]),
        )
        for row in results
    ]


def get_category_performance(user_id: str) -> list[CategoryPerformance]:
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
                        {"$ifNull": ["$category", "Uncategorized"]},
                    ]
                },
                "revenue": {"$sum": "$revenue"},
                "sales_count": {"$sum": 1},
            }
        },
        {"$sort": {"revenue": -1}},
        {
            "$project": {
                "_id": 0,
                "category": "$_id",
                "revenue": 1,
                "sales_count": 1,
            }
        },
    ]

    results = _run_aggregation(_get_sales_collection(), pipeline)
    return [
        CategoryPerformance(
            category=row["category"],
            revenue=float(row["revenue"]),
            sales_count=int(row["sales_count"]),
        )
        for row in results
    ]


def get_analytics_summary(user_id: str) -> AnalyticsSummary:
    collection = _get_sales_collection()

    totals_pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "total_profit": {"$sum": "$profit"},
                "total_sales": {"$sum": 1},
            }
        },
    ]

    top_product_pipeline = [
        {"$match": {"user_id": user_id}},
        {
            "$group": {
                "_id": "$product_name",
                "quantity_sold": {"$sum": "$quantity"},
            }
        },
        {"$sort": {"quantity_sold": -1}},
        {"$limit": 1},
    ]

    best_category_pipeline = [
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
                        {"$ifNull": ["$category", "Uncategorized"]},
                    ]
                },
                "revenue": {"$sum": "$revenue"},
            }
        },
        {"$sort": {"revenue": -1}},
        {"$limit": 1},
    ]

    totals_results = _run_aggregation(collection, totals_pipeline)
    top_product_results = _run_aggregation(collection, top_product_pipeline)
    best_category_results = _run_aggregation(collection, best_category_pipeline)

    if not totals_results:
        return AnalyticsSummary(
            total_revenue=0.0,
            total_profit=0.0,
            total_sales=0,
            top_product=None,
            best_category=None,
            average_order_value=0.0,
            repeat_customers_pct=0.0,
        )

    totals = totals_results[0]
    total_revenue = float(totals["total_revenue"])
    total_profit = float(totals["total_profit"])
    total_sales = int(totals["total_sales"])
    top_product = (
        top_product_results[0]["_id"] if top_product_results else None
    )
    best_category = (
        best_category_results[0]["_id"] if best_category_results else None
    )
    aov = round(total_revenue / total_sales, 2) if total_sales > 0 else 0.0

    return AnalyticsSummary(
        total_revenue=total_revenue,
        total_profit=total_profit,
        total_sales=total_sales,
        top_product=top_product,
        best_category=best_category,
        average_order_value=aov,
        repeat_customers_pct=0.0,
    )
