"""Response DTOs: the only customer data the API exposes; the entity is never serialized directly."""

import datetime as dt
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr

from app.domain.entities import CustomerStatus


class CustomerResponse(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    status: CustomerStatus
    created_at: dt.datetime


class DailyRegistrationsResponse(BaseModel):
    date: dt.date
    count: int


class CustomerSummaryResponse(BaseModel):
    total: int
    by_status: dict[CustomerStatus, int]
    registrations: list[DailyRegistrationsResponse]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
