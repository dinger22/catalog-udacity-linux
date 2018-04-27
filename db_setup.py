import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    user_id = Column(Integer, primary_key=True)
    user_name = Column(String(128), nullable=False)
    user_email = Column(String(256), nullable=False)

class Category(Base):
    """
    categories
    """
    __tablename__ = 'category'
    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(128), nullable=False)
    items=[]
    @property
    def serialize(self):
        return {
            'category_id': self.category_id,
            'category_name': self.category_name,
            'items': self.items
        }


class Item(Base):
    """
    items belong to categories
    """
    __tablename__ = 'catalog_item'

    catalog_item_id = Column(Integer, primary_key=True)
    catalog_item_name = Column(String(64), nullable=False)
    catalog_item_description = Column(String(128))
    catalog_item_category_id = Column(Integer, ForeignKey('category.category_id'))
    user_id = Column(Integer, ForeignKey('user.user_id'))
    
    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'catalog_item_id': self.catalog_item_id,
            'catalog_item_name': self.catalog_item_name,
            'catalog_item_description': self.catalog_item_description,
            'user_id': self.user_id
        }


