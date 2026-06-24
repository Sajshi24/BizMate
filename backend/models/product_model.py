from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    cost_price: float = Field(..., ge=0)
    selling_price: float = Field(..., ge=0)
    stock: int = Field(..., ge=0)
    minimum_stock: int = Field(..., ge=0)
    supplier: str = Field(..., min_length=1, max_length=200)


class ProductCreate(ProductBase):
    """Payload for creating a new product."""


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    category: str | None = Field(default=None, min_length=1, max_length=100)
    cost_price: float | None = Field(default=None, ge=0)
    selling_price: float | None = Field(default=None, ge=0)
    stock: int | None = Field(default=None, ge=0)
    minimum_stock: int | None = Field(default=None, ge=0)
    supplier: str | None = Field(default=None, min_length=1, max_length=200)


class ProductResponse(ProductBase):
    product_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProductDeleteResponse(BaseModel):
    success: bool = True
    message: str
    product_id: str
