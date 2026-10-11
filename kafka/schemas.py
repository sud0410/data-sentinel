from datetime import datetime
from decimal import Decimal
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class TransactionCategory(str, Enum):
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    HEALTHCARE = "healthcare"
    RETAIL = "retail"
    UTILITIES = "utilities"
    TRAVEL = "travel"
    OTHER = "other"


class TransactionEvent(BaseModel):
    transaction_id: UUID
    user_id: str = Field(..., min_length=1)
    merchant: str = Field(..., min_length=1)
    category: TransactionCategory
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    timestamp: datetime
    metadata: dict = Field(default_factory=dict)

    @field_validator("currency")
    @classmethod
    def currency_uppercase(cls, v: str) -> str:
        return v.upper()

    model_config = {"json_encoders": {Decimal: str, UUID: str}}
