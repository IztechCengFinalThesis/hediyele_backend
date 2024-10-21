from pydantic import BaseModel, Field
from typing import List, Optional

# Book Schema
class BookBase(BaseModel):
    title: str = Field(..., max_length=255, description="Title of the book")
    author: str = Field(..., max_length=255, description="Author of the book")
    publisher: str = Field(..., max_length=255, description="Publisher of the book")
    price: float = Field(..., gt=0, description="Price of the book, must be a positive value")
    currency: str = Field(..., max_length=10, description="Currency of the price, e.g., USD, EUR")
    description: Optional[str] = Field(None, description="Optional description of the book")
    url: Optional[str] = Field(None, max_length=255, description="Optional URL for more information about the book")

class BookCreate(BookBase):
    pass

class Book(BookBase):
    id: int = Field(..., description="Unique identifier for the book")

    class Config:
        orm_mode = True

# Category Schema
class CategoryBase(BaseModel):
    category_name: str = Field(..., description="Name of the category")

class CategoryCreate(CategoryBase):
    pass

class Category(CategoryBase):
    id: int = Field(..., description="Unique identifier for the category")

    class Config:
        orm_mode = True

# CategoriesVectorized Schema
class CategoriesVectorizedBase(BaseModel):
    category_id: int = Field(..., description="ID of the category this vector belongs to")
    vector: List[float] = Field(..., description="A vector representation of the category")

class CategoriesVectorizedCreate(CategoriesVectorizedBase):
    pass

class CategoriesVectorized(CategoriesVectorizedBase):
    id: int = Field(..., description="Unique identifier for the vectorized category")

    class Config:
        orm_mode = True
