import csv
import io
import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from pymongo.errors import PyMongoError

from backend.models.product_model import (
    ProductCreate,
    ProductDeleteResponse,
    ProductResponse,
    ProductUpdate,
)
from backend.models.user_model import UserResponse
from backend.routes.deps import get_current_user
from backend.services import product_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/products", tags=["Products"])

# Required CSV columns
_REQUIRED_CSV_COLUMNS = {
    "name",
    "category",
    "cost_price",
    "selling_price",
    "stock",
    "minimum_stock",
    "supplier",
}


class CsvImportResponse(BaseModel):
    imported: int
    message: str


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a product",
)
def create_product(
    payload: ProductCreate,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    try:
        return product_service.create_product(payload, current_user.user_id)
    except PyMongoError as exc:
        logger.error("Database error while creating product: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.get(
    "",
    response_model=list[ProductResponse],
    summary="List all products for the authenticated user",
)
def list_products(
    current_user: UserResponse = Depends(get_current_user),
) -> list[ProductResponse]:
    try:
        return product_service.get_all_products(current_user.user_id)
    except PyMongoError as exc:
        logger.error("Database error while listing products: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.post(
    "/import-csv",
    response_model=CsvImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import products from a CSV file",
)
async def import_products_csv(
    file: UploadFile = File(...),
    current_user: UserResponse = Depends(get_current_user),
) -> CsvImportResponse:
    """
    Upload a CSV file to bulk-import products into the authenticated user's account.

    Required columns: name, category, cost_price, selling_price, stock, minimum_stock, supplier
    """
    # Validate file type
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file type. Please upload a .csv file.",
        )

    content = await file.read()
    if not content.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded CSV file is empty.",
        )

    try:
        text = content.decode("utf-8-sig")  # Handle BOM if present
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not decode the CSV file. Please ensure it is UTF-8 encoded.",
        )

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The CSV file has no header row.",
        )

    actual_columns = {col.strip().lower() for col in reader.fieldnames}
    missing_columns = _REQUIRED_CSV_COLUMNS - actual_columns
    if missing_columns:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV upload failed: missing required column(s): {', '.join(sorted(missing_columns))}.",
        )

    rows = list(reader)
    if not rows:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The CSV file contains no data rows.",
        )

    products_to_create: list[ProductCreate] = []
    errors: list[str] = []

    for i, raw_row in enumerate(rows, start=2):  # Row 1 is header
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items()}

        name = row.get("name", "").strip()
        category = row.get("category", "").strip()
        supplier = row.get("supplier", "").strip()

        if not name:
            errors.append(f"Row {i}: 'name' is required.")
            continue
        if not category:
            errors.append(f"Row {i}: 'category' is required.")
            continue
        if not supplier:
            errors.append(f"Row {i}: 'supplier' is required.")
            continue

        try:
            cost_price = float(row.get("cost_price", ""))
            if cost_price < 0:
                raise ValueError("must be >= 0")
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'cost_price' must be a non-negative number.")
            continue

        try:
            selling_price = float(row.get("selling_price", ""))
            if selling_price < 0:
                raise ValueError("must be >= 0")
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'selling_price' must be a non-negative number.")
            continue

        try:
            stock = int(float(row.get("stock", "")))
            if stock < 0:
                raise ValueError("must be >= 0")
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'stock' must be a non-negative integer.")
            continue

        try:
            minimum_stock = int(float(row.get("minimum_stock", "")))
            if minimum_stock < 0:
                raise ValueError("must be >= 0")
        except (ValueError, TypeError):
            errors.append(f"Row {i}: 'minimum_stock' must be a non-negative integer.")
            continue

        products_to_create.append(
            ProductCreate(
                name=name,
                category=category,
                cost_price=cost_price,
                selling_price=selling_price,
                stock=stock,
                minimum_stock=minimum_stock,
                supplier=supplier,
            )
        )

    if errors and not products_to_create:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"CSV upload failed. All rows had errors: {'; '.join(errors[:5])}",
        )

    imported_count = 0
    try:
        for payload in products_to_create:
            product_service.create_product(payload, current_user.user_id)
            imported_count += 1
    except PyMongoError as exc:
        logger.error("Database error during CSV import for user %s: %s", current_user.user_id, exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database error after importing {imported_count} products. Please try again.",
        ) from exc

    message = f"Successfully imported {imported_count} product{'s' if imported_count != 1 else ''}."
    if errors:
        message += f" {len(errors)} row(s) were skipped due to errors."

    logger.info(
        "CSV import: user %s imported %d products (%d errors)",
        current_user.user_id,
        imported_count,
        len(errors),
    )
    return CsvImportResponse(imported=imported_count, message=message)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get a product by ID",
)
def get_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    try:
        return product_service.get_product_by_id(
            product_id,
            current_user.user_id,
        )
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error(
            "Database error while fetching product %s: %s",
            product_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update a product",
)
def update_product(
    product_id: str,
    payload: ProductUpdate,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductResponse:
    try:
        return product_service.update_product(
            product_id,
            payload,
            current_user.user_id,
        )
    except product_service.ProductValidationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error(
            "Database error while updating product %s: %s",
            product_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc


@router.delete(
    "/{product_id}",
    response_model=ProductDeleteResponse,
    summary="Delete a product",
)
def delete_product(
    product_id: str,
    current_user: UserResponse = Depends(get_current_user),
) -> ProductDeleteResponse:
    try:
        deleted_id = product_service.delete_product(
            product_id,
            current_user.user_id,
        )
        return ProductDeleteResponse(
            message="Product deleted successfully",
            product_id=deleted_id,
        )
    except product_service.ProductNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except PyMongoError as exc:
        logger.error(
            "Database error while deleting product %s: %s",
            product_id,
            exc,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is unavailable. Please try again later.",
        ) from exc