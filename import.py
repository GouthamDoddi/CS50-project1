import csv
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
# from models import db

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


def main():
    f = open('books.csv')
    books = csv.DictReader(f)
    for book_data in books:
        book_data['year'] = int(book_data['year'])
        db.execute("INSERT INTO book (isbn, title, author, published_on) VALUES (:isbn, :title, :author, :year) ON CONFLICT DO NOTHING",
                     book_data)
        db.commit()


if __name__ == "__main__":
    main()