import os
import requests
from flask import (Flask, render_template, request,
                   redirect, url_for,
                   flash, session, jsonify)
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
    return render_template('LogIn.html')


def logged_out(some_func):
    def wrap_func():
        if session['logged_in'] is not None:
            flash('User {} must log out first'.format(session['logged_in']))
            return render_template('profile.html')
        else:
            return some_func()

    wrap_func.__name__ = some_func.__name__
    return wrap_func


def logged_in(some_func):
    def wrap_func():
        if session['logged_in'] is None:
            flash('User must login first!')
            return render_template('Login.html')
        else:
            return some_func()

    wrap_func.__name__ = some_func.__name__
    return wrap_func


@app.route("/register", methods=['GET', 'POST'])
@logged_out
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
@logged_out
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
@logged_in
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
@logged_in
def books():
    global isbn
    isbn = []
    result = []
    books = []
    reviews = []
    post_reviews = []
    if request.method == 'POST':

        # The below func gets the keyword that will be used to search for matching books
        keyword = request.form.get('keyword')
        print("{} is the key".format(keyword))
        results = db.execute("""SELECT * FROM book WHERE isbn LIKE '%{}%'  OR title LIKE '%{}%' OR author LIKE '%{}%'"""
                             .format(keyword, keyword, keyword)).fetchall()
        print(f"{results} is the matching books data")

        # The below func helps us to display all the site users's comments under
        # each book
        for key2 in results:
            review = db.execute("""SELECT * FROM review WHERE book = :isbn""", {'isbn': key2[3]}).fetchall()

            # creating dict objects for post_reviews list
            post_review_dict = {'book': key2[3], 'reviewed_by': session['logged_in']}
            post_reviews.append(post_review_dict)

            print(review)

            reviews.append(review)
        print(reviews)

        # adding avg rating and no of reviews from site user review data
        # for review in reviews:
        #     if review is not []:
        #         for each_review in review:
        #             if each_review is []:
        #                 continue
        #             else:
        #                 list_of_ratings.append(each_review[3])
        #                 isbn = each_review[2]
        #         total_reviews = len(list_of_ratings)
        #         print(total_reviews)
        #         if total_reviews == 0:
        #             average_rating = 0
        #             isbn = None
        #         else:
        #             average_rating = sum(list_of_ratings) // total_reviews
        #         print(average_rating)
        #         print(isbn)
        #           db.execute("""UPDATE book SET average_rating = :average_rating, total_reviews = :total_reviews
        #                    WHERE isbn=:isbn""",
        #                     {'average_rating': average_rating, 'total_reviews': total_reviews, 'isbn': isbn})
        #           db.commit()

        # the below fuc gets info fron good reads about reviews and displays it on site
        for key in results:
            print(key)

            books.append(key[3])
            res = requests.get("https://www.goodreads.com/book/review_counts.json",
                               params={"key": "3HOY8QuwJY4iFDPh6YbQ", "isbns": key[3]})
            json_result = res.json()
            key_d = dict(key.items())
            key_d['total_reviews'] = json_result['books'][0]['ratings_count']
            key_d['average_rating'] = json_result['books'][0]['average_rating']
            result.append(key_d)

        print(result)

        return render_template('books.html', result=[result, reviews, post_reviews])


@app.route("/adding_review", methods=['GET', 'POST'])
def adding_review():
    # The route takes care of checking and posting the review data by the site users.
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


@app.route('/api/<isbns>')
def books_api(isbns):
    # this route lets users get json data from the site.
    print(isbns)
    book_data = db.execute("""SELECT * FROM book WHERE isbn=:isbn""", {'isbn': isbns}).fetchone()
    print(book_data)
    if book_data is None:
        return "<h1> no books with such isbn </h1>"

    def creating_dict(row):
        api_dict = {'title': row[0], 'author': row[1], 'year': row[2], 'isbn': row[3]}
        return api_dict
    json_obj = (creating_dict(book_data))
    return json_obj
