from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SimpleSchema(BaseModel):
    """Simple schema 1."""

    id: UUID = Field(description="id")
    name: str = Field(description="name")
    created_at: datetime = Field(description="created at")
    updated_at: datetime = Field(description="updated at")


class CreateSimpleSchema(BaseModel):
    """Create simple schema."""

    name: str = Field(description="name")
