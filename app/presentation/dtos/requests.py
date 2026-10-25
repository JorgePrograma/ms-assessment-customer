from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.domain.entities import CustomerStatus


class CreateCustomerRequest(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
        json_schema_extra={"examples": [{"name": "Juan Pérez", "email": "juan@example.com"}]},
    )

    name: str = Field(min_length=1, max_length=120)
    email: EmailStr


class UpdateCustomerStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", json_schema_extra={"examples": [{"status": "ACTIVE"}]})

    status: CustomerStatus
