from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os

db = SQLAlchemy()


class Man(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return self.username


class Book(db.Model):
    __tablename__ = "book"
    title = db.Column(db.String(50), nullable=False)
    author = db.Column(db.String(50), unique=False, nullable=False)
    published_on = db.Column(db.Integer, nullable=False)
    isbn = db.Column(db.String(10), primary_key=True)
    average_rating = db.Column(db.Float)
    total_reviews = db.Column(db.Integer)

    def __repr__(self):
        return self.isbn


class Review(db.Model):
    __tablename__ = "review"
    review_id = db.Column(db.Integer, primary_key=True)
    review = db.Column(db.Text)
    reviewed_by = db.Column(db.Integer, db.ForeignKey("user.user_id"), nullable=False)
    book = db.Column(db.String(10), db.ForeignKey("book.isbn"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return self.review_id
