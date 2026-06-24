from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
    product_id: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)


class SaleResponse(BaseModel):
    sale_id: str
    product_id: str
    product_name: str
    quantity: int = Field(..., gt=0)
    unit_cost: float = Field(..., ge=0)
    unit_price: float = Field(..., ge=0)
    revenue: float = Field(..., ge=0)
    cost: float = Field(..., ge=0)
    profit: float
    sale_date: datetime

    model_config = ConfigDict(from_attributes=True)
