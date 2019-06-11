# -*- coding: utf-8 -*-
""" Module with the models of the project Item Catalog

This module has three classes:
    - User: the class that creates the table of the users;
    - Category: the class that creates the table of the categories;
    - CategoryItem: the class that creates the table of the category items.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///item_catalog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class User(db.Model):
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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), nullable=False)
    email = db.Column(db.String(250), nullable=False)
    picture = db.Column(db.String(250))

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
            'id': self.id,
            'name': self.name,
            'email': self.email}


class Category(db.Model):
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

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(250), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)

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
            'id': self.id,
            'name': self.name}


class CategoryItem(db.Model):
    """
    The class that creates the table of the category items.

    Attributes:
    -----------
    id : Integer
        Primary key of the table
    title : String(250)
        The title of the item
    description : Text
        The description of the item
    cat_id : Integer
        The category id that the item belongs
    user_id : Integer
        The user id that created the category

    Methods:
    --------
    serialize()
        Return a dictionary with information about the item.
    """

    __tablename__ = 'categoryitem'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    description = db.Column(db.Text)
    cat_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship(
        Category,
        backref=db.backref("categoryitem", cascade="all, delete-orphan"))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship(User)

    @property
    def serialize(self):
        """
        Return a dictionary with information about the item.

        Returns:
        --------
        dictionary
            Information about the item: id, title, description and cat_id.
        """
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'cat_id': self.cat_id}


# If run this module will create all tables.
if __name__ == '__main__':
    db.create_all()
