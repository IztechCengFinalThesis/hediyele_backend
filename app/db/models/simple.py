from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from db.models.base import BaseModel


class SimpleModel(BaseModel):
    """Simple model."""

    name: Mapped[str] = mapped_column(String(128), nullable=False)
