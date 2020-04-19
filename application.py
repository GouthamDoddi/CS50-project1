import os
from flask import (Flask, render_template, request,
                   redirect, url_for,
                   flash, session)
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import sqlalchemy
from project1.models import db

app = Flask(__name__)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATABASE_URL")

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
# db.init_app(app)
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
def index():
    return "Login or registere to vew the content in the site."


def logged_in(some_func):
    def wrap_func():
        if session['logged_in'] is not None:
            flash('User {} must log out first'.format(session['logged_in']))
            return render_template('profile.html')
        else:
            return some_func()

    wrap_func.__name__ = some_func.__name__
    return wrap_func


def logged_out(some_func):
    def wrap_func():
        if session['logged_in'] is None:
            flash('User must login first!')
            return render_template('Login.html')
        else:
            return some_func()

    wrap_func.__name__ = some_func.__name__
    return wrap_func


@app.route("/register", methods=['GET', 'POST'])
@logged_in
def register():
    if request.method == 'POST':
        # getting info
        username = request.form.get('username')
        password = request.form.get("password")
        print(f"{username}, {password}")
        # save info

        try:
            db.execute("""INSERT INTO "user" (username, password) VALUES (:username, :password)""",
                       {'username': username, 'password': password})
            db.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("Username already exists. Please choose another.")
            return render_template('register.html')
        else:
            print(f"The {username} and {password} have been added into the database.")
            flash(f"User '{username}' has been registered! Try logging in.")
            return render_template('login.html')
    return render_template("register.html")


@app.route("/login", methods=['POST', 'GET'])
@logged_in
def login():
    if request.method == 'POST':
        # get info
        username = request.form.get("username")
        password = request.form.get("password")
        print(password)

        # # validating LogIn info
        try:
            user = db.execute("""SELECT user_id FROM "user" WHERE username= :usern AND password= :passw""",
                              {'usern': username, 'passw': password}).fetchone()
            # user1 = db.engine.execute("select column_name from information_schema.columns where table_name= %s", table)
            print(user)
        except:
            flash("can't find the user!")
            return redirect(url_for("login"))
        else:
            if user is not None:
                session['logged_in'] = username
                flash("You have logged in with {}. You can now search for books and leave a review.".format(username))
                print(session['logged_in'])
                return render_template("profile.html")
            else:
                flash("Improper credentials!")
                return render_template('profile.html')

    return render_template("login.html")


@app.route("/logout", methods=['GET', 'POST'])
@logged_out
def logout():
    if session['logged_in'] is None:
        flash('User must login first!')
        return redirect(url_for('login'))
    else:
        if request.method == 'POST':
            session['logged_in'] = None
            flash("You have logged out. You can try logging in again if you want to visit the website.")
            return render_template('Login.html')
        return render_template('logout.html')


@app.route("/books", methods=['GET', 'POST'])
@logged_out
def books():
    result = []
    books = []
    reviews = []
    post_reviews = []
    if request.method == 'POST':
        keyword = request.form.get('keyword')
        results = db.execute("""SELECT * FROM book WHERE isbn LIKE '%{}%'  OR title LIKE '%{}%' OR author LIKE '%{}%'"""
                             .format(keyword, keyword, keyword)).fetchall()
        for key in results:
            review = db.execute("""SELECT * FROM review WHERE book = :isbn""", {'isbn': key[3]}).fetchone()

            # creating dict objects for post_reviews list
            post_review_dict = {}
            post_review_dict['book'] = key[3]
            post_review_dict['reviewed_by'] = session['logged_in']
            post_reviews.append(post_review_dict)

            print(review)

            reviews.append(review)
            # adding foreign keys to review dict

            d = dict(key.items())
            if d['average_rating'] is None:
                d['average_rating'] = 0
            if d['total_reviews'] is None:
                d['total_reviews'] = 0
                result.append(d)
                books.append(d['isbn'])
                # converted lists to dictionaries
        print(result)
        # for book in books:
        #         review = db.execute("""SELECT * FROM review WHERE book = :isbn""", {'isbn': book}).fetchone()
        #         if review is not None:
        #             reviews.append(review)
        # print(reviews)
        return render_template('books.html', result=[result, reviews, post_reviews])


@app.route("/adding_review", methods=['GET', 'POST'])
def adding_review():
    if request.method == 'POST':
        review = request.form.get('review')
        book = request.form.get('book')
        rating = request.form.get('rating')
        reviewed_by = request.form.get('reviewed_by')
        review_obj = db.execute("""SELECT * FROM review WHERE reviewed_by = :reviewed_by AND book = :book""",
                      {'reviewed_by': reviewed_by, 'book': book}).fetchone()
        if review_obj is None:
            try:
                db.execute("""INSERT INTO review(review, book, rating, reviewed_by) 
                        VALUES(:review, :book, :rating, :reviewed_by)""",
                            {'review': review, 'book': book, 'rating': rating, 'reviewed_by': reviewed_by})
                db.commit()
                print('done')
            except:
                flash("check you info and try again")
                return render_template('profile.html')
            else:
                flash("You have added review for {}".format(book))
                return render_template('profile.html')
        else:
            flash('You can only review a book once')
            return render_template('profile.html')
    else:
        return redirect(url_for('books'))




