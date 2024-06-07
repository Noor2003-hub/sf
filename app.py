import os
import random
import cs50
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, valid_name, get_name, get_pic, similar, song_name, get_song_pic, \
    get_song_date
from test import get_songs
import numpy as np

# Configure application
app = Flask(__name__)

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")


@app.route('/about/')
def about():
    return render_template("about.html")


@app.route('/finish/')
def finish():
    return render_template("finish.html", artist=session.get('random_artist', []))


@app.route('/correct/', methods=["GET", "POST"])
def correct():
    return render_template("correct.html", artist=session.get('random_artist', []), done=True)


@app.route('/game/', methods=["GET", "POST"])
def game():
    if request.method == "GET":
        if 'fav_names' not in session or len(session['fav_names']) < 1:
            flash("You can't play without choosing at least 1 artist!")
            return render_template("new.html", fav_names=session.get('fav_names', []))

        score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']
        return render_template("game.html", artist=session.get('random_artist', []), score=score)
    else:
        if 'random_artist' not in session or len(session['random_artist']) < 1:
            return apology("Game was interrupted. Please start a new game.")

        name = session['random_artist'][0]
        answer = request.form.get("answer")
        song = song_name(answer, name)

        if request.form.get("answer"):
            if answer.lower() == song.lower() or similar(answer.lower(), song.lower()) > 0.7:
                flash("Correct!")
                score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']
                total = score + 50
                db.execute("UPDATE users SET score = ? WHERE id = ?", total, session["user_id"])

                high = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['high']
                if total > high:
                    db.execute("UPDATE users SET high = ? WHERE id = ?", total, session["user_id"])

                song_pic = get_song_pic(answer, name)
                song_date = get_song_date(answer, name)

                return render_template("correct.html", artist=session['random_artist'], song=song, song_pic=song_pic,
                                       song_date=song_date, score=total, done=True)

            flash("Try Again.")
            score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']
            return render_template("game.html", artist=session['random_artist'], done=False, score=score)
        else:
            flash(f"Please enter track title that starts with {session['random_artist'][2]}")
            score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']
            return render_template("game.html", artist=session['random_artist'], done=False, score=score)


@app.route('/my-link/')
def my_link():
    session['fav_names'] = []
    session['fav_pics'] = []
    session['appered'] = []
    return render_template("new.html", fav_names=session['fav_names'])


@app.route('/my-link2/')
def my_link2():
    try:
        score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']

        if 'fav_names' not in session or len(session['fav_names']) < 1:
            flash("Please enter an artist name to start the game.")
            return render_template("new.html", fav_names=session.get('fav_names', []))

        name = random.choice(session['fav_names'])
        session['random_artist'] = [name, get_pic(name)]
        songs = get_songs(name)

        letters = []
        for song in songs:
            if song != '' and song[0] not in session.get('appered', []):
                letters.append(song[0])

        if len(letters) < 1 and score > 0:
            session['fav_pics'] = [get_pic(n) for n in session['fav_names']]
            return render_template("finish.html", fav_names=session['fav_names'], fav_pics=session['fav_pics'],
                                   score=score)
        else:
            random_letter = random.choice(letters)
            session['random_artist'].append(random_letter)
            session.setdefault('appered', []).append(random_letter)
            return render_template("game.html", artist=session['random_artist'], score=score)
    except Exception as e:
        return apology('Timed out! Please refresh this page')


@app.route('/my-link3/')
def my_link3():
    session['random_artist'] = []
    return my_link2()


@app.route('/my-link4/')
def my_link4():
    score = db.execute("SELECT * FROM users WHERE id=?", session["user_id"])[0]['score']
    total = max(0, score - 25)
    db.execute("UPDATE users SET score = ? WHERE id = ?", total, session["user_id"])
    return my_link3()


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    db.execute("UPDATE users SET score = ? WHERE id = ?", 0, session["user_id"])

    if request.method == "GET":
        return render_template("new.html", fav_names=session.get('fav_names', []))
    else:
        try:
            artist = request.form.get("artist")
            if not artist:
                flash("Please enter an artist name to start the game.")
                return render_template("new.html", fav_names=session.get('fav_names', []))
            if not valid_name(artist):
                flash("Sorry! But this artist is unavailable")
                return render_template("new.html", fav_names=session.get('fav_names', []))
            if artist in session.get('fav_names', []):
                flash(f"{artist} already exists!")
                return render_template("new.html", fav_names=session.get('fav_names', []))

            session.setdefault('fav_names', []).append(get_name(artist))
            session.setdefault('fav_pics', []).append(get_pic(artist))
            return render_template("new.html", fav_names=session['fav_names'])
        except Exception as e:
            return apology("Timed out. Please try to refresh the page")


@app.route("/")
@login_required
def index():
    db.execute("UPDATE users SET score = ? WHERE id = ?", 0, session["user_id"])
    session['fav_names'] = []
    session['fav_pics'] = []
    session['appered'] = []
    session['random_artist'] = []

    user = db.execute("SELECT username, high FROM users WHERE id=?", session["user_id"])[0]
    return render_template("index.html", name=user["username"], score=user["high"])


@app.route("/login", methods=["GET", "POST"])
def login():
    session.clear()

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if not username or not password:
            return apology("Must provide username and password", 403)

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)

        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], password):
            return apology("Invalid username and/or password", 403)

        session["user_id"] = rows[0]["id"]
        return redirect("/")
    else:
        return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        if not username or not password or not confirmation:
            return apology("Username or password is empty.")
        if db.execute("SELECT * FROM users WHERE username = ?", username):
            return apology("Username already exists.")
        if password != confirmation:
            return apology("Passwords do not match.")
        if len(password) < 4:
            return apology("Password should be longer than 4 characters")

        has_num = any(char.isdigit() for char in password)
        has_special = any(char in set("[@_!#$%^&*()<>?/|}{~:]") for char in password)

        if not has_num or not has_special:
            return apology("Password should contain at least 1 digit and at least 1 special character")

        db.execute("INSERT INTO users (username, hash, score) VALUES(?, ?, ?)", username,
                   generate_password_hash(password), 0)
        user = db.execute("SELECT * FROM users WHERE username = ?", username)[0]
        session["user_id"] = user["id"]
        return redirect("/")

    return render_template("register.html")


if __name__ == "__main__":
    app.run(debug=True)
