from sqlalchemy import ARRAY, Column, Float, Integer, Numeric, String, Text, text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata

class Book(Base):
    __tablename__ = 'book'

    id = Column(Integer, primary_key=True, server_default=text("nextval('book_id_seq'::regclass)"))
    title = Column(String(255))
    author = Column(String(255))
    publisher = Column(String(255))
    price = Column(Numeric)
    currency = Column(String(10))
    description = Column(Text)
    url = Column(String(255))


class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, server_default=text("nextval('categories_id_seq'::regclass)"))
    category_name = Column(Text)


class CategoriesVectorized(Base):
    __tablename__ = 'categories_vectorized'

    id = Column(Integer, primary_key=True, server_default=text("nextval('categories_vectorized_id_seq'::regclass)"))
    category_id = Column(Integer)
    vector = Column(ARRAY(Float(precision=53)))
