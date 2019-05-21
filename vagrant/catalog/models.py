# -*- coding: utf-8 -*-
""" Module with the models of the project Item Catalog

This module has three classes:
    - User: the class that creates the table of the users;
    - Category: the class that creates the table of the categories;
    - CategoryItem: the class that creates the table of the category items.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import relationship

# Returns a new base class from which all mapped classes should inherit
Base = declarative_base()

class User(Base):
    """
    The class that creates the table of the users.

    Attributes:
    -----------
    id : Integer
        Primary key of the table
    name : String(250)
        The name of the user
    email : String(250)
        The email of the user
    picture : String(250)
        The path to the picture of the user

    Methods:
    --------
    serialize()
        Return a dictionary with information about the user.
    """

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    email = Column(String(250), nullable=False)
    picture = Column(String(250))

    @property
    def serialize(self):
        """
        Return a dictionary with information about the user.

        Returns:
        --------
        dictionary
            Information about the user: id, name and email.
        """
        return {
            'id' : self.id,
            'name': self.name,
            'email' : self.email,}

class Category(Base):
    """
    The class that creates the table of the categories.

    Attributes:
    -----------
    id : Integer
        Primary key of the table
    name : String(250)
        The name of the category
    user_id : Integer
        The user id that created the category

    Methods:
    --------
    serialize()
        Return a dictionary with information about the category.
    """

    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(250), nullable=False)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """
        Return a dictionary with information about the category.

        Returns:
        --------
        dictionary
            Information about the category: id and name.
        """
        return {
            'id' : self.id,
            'name': self.name,}

class CategoryItem(Base):
    """
    The class that creates the table of the category items.

    Attributes:
    -----------
    id : Integer
        Primary key of the table
    name : String(250)
        The name of the category
    user_id : Integer
        The user id that created the category

    Methods:
    --------
    serialize()
        Return a dictionary with information about the category.
    """
    __tablename__ = 'category_item'

    id = Column(Integer, primary_key=True)
    title = Column(String(250), nullable=False)
    description = Column(Text)
    cat_id = Column(Integer,ForeignKey('category.id'))
    category = relationship(Category)
    user_id = Column(Integer,ForeignKey('user.id'))
    user = relationship(User)

# Create an engine that stores data in the local directory's
engine = create_engine('sqlite:///item_catalog.db')

# Create all tables in the engine.
Base.metadata.create_all(engine)
