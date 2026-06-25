import logging
from dataclasses import dataclass

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


def _get_sales_collection() -> Collection:
    return db[SALES_COLLECTION]


def _run_aggregation(collection: Collection, pipeline: list) -> list:
    try:
        return list(collection.aggregate(pipeline))
    except PyMongoError as exc:
        logger.error("Analytics aggregation failed: %s", exc)
        raise


def get_sales_trend() -> list[SalesTrendPoint]:
    pipeline = [
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


def get_revenue_trend() -> list[RevenueTrendPoint]:
    pipeline = [
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


def get_top_products() -> list[TopProduct]:
    pipeline = [
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


def get_category_performance() -> list[CategoryPerformance]:
    pipeline = [
        {
            "$lookup": {
                "from": PRODUCTS_COLLECTION,
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "product",
            }
        },
        {"$unwind": "$product"},
        {
            "$group": {
                "_id": "$product.category",
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


def get_analytics_summary() -> AnalyticsSummary:
    totals_pipeline = [
        {
            "$group": {
                "_id": None,
                "total_revenue": {"$sum": "$revenue"},
                "total_profit": {"$sum": "$profit"},
                "total_sales": {"$sum": 1},
            }
        }
    ]

    top_product_pipeline = [
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
        {
            "$lookup": {
                "from": PRODUCTS_COLLECTION,
                "localField": "product_id",
                "foreignField": "product_id",
                "as": "product",
            }
        },
        {"$unwind": "$product"},
        {
            "$group": {
                "_id": "$product.category",
                "revenue": {"$sum": "$revenue"},
            }
        },
        {"$sort": {"revenue": -1}},
        {"$limit": 1},
    ]

    collection = _get_sales_collection()

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
        )

    totals = totals_results[0]
    top_product = (
        top_product_results[0]["_id"] if top_product_results else None
    )
    best_category = (
        best_category_results[0]["_id"] if best_category_results else None
    )

    return AnalyticsSummary(
        total_revenue=float(totals["total_revenue"]),
        total_profit=float(totals["total_profit"]),
        total_sales=int(totals["total_sales"]),
        top_product=top_product,
        best_category=best_category,
    )
