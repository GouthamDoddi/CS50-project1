import os

from flask import Flask
from models import db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False


def main():
    db.init_app(app)
    db.create_all()
    # username = "Testman"
    # password = "Passman"
    # db.engine.execute('INSERT INTO "user" (username, password) VALUES (%s, %s);',
    #                   (username, password))


if __name__ == "__main__":
    with app.app_context():
        main()
