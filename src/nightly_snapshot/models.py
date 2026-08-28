from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Checkout(StrictModel):
    checkout_id: str
    customer_id: str
    currency: str = Field(min_length=3, max_length=3)
    total: Decimal = Field(ge=0)
    placed_at: datetime


class Fulfillment(StrictModel):
    order_id: str
    status: Literal["pending", "packed", "shipped", "delivered"]
    updated_at: datetime


class Receipt(StrictModel):
    receipt_id: str
    order_id: str
    amount: Decimal = Field(ge=0)
    issued_at: datetime


class CustomerOrderUpdate(StrictModel):
    customer_id: str
    order_id: str
    state: Literal["placed", "paid", "fulfilled", "cancelled"]
    changed_at: datetime


class SnapshotRequest(StrictModel):
    snapshot_date: date
    checkouts: list[Checkout]
    fulfillments: list[Fulfillment]
    receipts: list[Receipt]
    customer_updates: list[CustomerOrderUpdate]


class SnapshotResult(StrictModel):
    bucket: str
    key: str
    status: Literal["created", "already_exists"]
    record_count: int

