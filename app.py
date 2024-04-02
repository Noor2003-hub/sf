import os
import random
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required,valid_name,get_name,get_pic,similar,song_name,get_song_pic,get_song_date
from test import get_songs
#import numpy as np

# Configure application
app = Flask(__name__)



# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")
fav_names=list(set()) #list(set) to avoid duplicating names of favorite artists
random_artist=[] #random artist for each round
appered=[] #letters appear for all rounds in game
fav_pics=[] #pics of favorite artists



@app.route('/about/')
def about(): #return about.html
    return render_template("about.html")


@app.route('/finish/')
def finish(): #return finish.html
    return render_template("finish.html",artist=random_artist)
    #return render_template("finish.html",artist=random_artist,done=True)




@app.route('/correct/', methods=["GET", "POST"])
def correct(): #return correct.html
    if request.method == "GET":
        return render_template("correct.html",artist=random_artist,done=True)
    else:
        return render_template("correct.html",artist=random_artist,done=True)





@app.route('/game/', methods=["GET", "POST"])
def game():
    if request.method == "GET":
        if len(fav_names)<1: #if no names, game won't start
            flash("You can't play without choosing at least 1 artist!")
            return render_template("new.html",fav_names=fav_names)


        score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']

        return render_template("game.html",artist=random_artist,score=score)
    else:
        if len(random_artist)<1: #if no names, game won't start
            return apology("Game was innterpted. please start new game")
        name=random_artist[0]
        answer=request.form.get("answer")
        song=song_name(answer,name)
        if request.form.get("answer"): #if user answer exist, and match the right answer or similar to it, 50 points will be added
            if answer.lower() == song.lower() or similar(answer.lower() , song.lower())>0.7:
                flash (f"Correct!")
                score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
                total=score+50
                db.execute("UPDATE users SET score = ? WHERE id = ?", total, session["user_id"])
                high = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['high']
                if total>high:
                    db.execute("UPDATE users SET high = ? WHERE id = ?", total, session["user_id"])
                song_pic= get_song_pic(answer,name)
                song_date= get_song_date(answer,name)
                return render_template("correct.html",artist=random_artist,song=song,song_pic=song_pic,song_date=song_date,score=score+50,done=True)
            flash ("Try Again.")  # if not match, prompt the user to try again
            score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
            return render_template("game.html",artist=random_artist,done=False,score=score)
        else:
            flash (f"Please Enter track title that starts with {random_artist[2]}")
            score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
            return render_template("game.html",artist=random_artist,done=False,score=score)




@app.route('/my-link/')
def my_link(): #when new game start, clears any data about previous game
    fav_names.clear()
    fav_pics.clear()
    appered.clear()
    return render_template("new.html",fav_names=fav_names)

@app.route('/my-link2/')
def my_link2(): #this method choose random artist for each round of the game
    try:
        score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
        if len(fav_names)<1:
            flash(f"please enter an artist name to start the game.")
            return render_template("new.html",fav_names=fav_names)
        name=random.choice(fav_names)
        random_artist.append(name)
        random_artist.append(get_pic(name))
        songs=get_songs(name)
        letters=[]
        #print(songs)
        for song in songs:
            if song !='':
                first=song[0]
                if first not in appered:
                    letters.append(first)
                    print('##',song)
            else:
                continue
        if len(letters)<1 and score>0: #if all possible letters appered, game will finish
            fav_pics.clear()
            for namee in fav_names:
                fav_pics.append(get_pic(namee))

            return render_template("finish.html",fav_names=fav_names,fav_pics=fav_pics,score=score)
        else: #if there still letters didnt appear in the game, use it for next round
            random_artist.append(random.choice(letters))
            appered.append(random_artist[2])
            print('\n\n\n\n',random_artist,'\n\n\n\n')
            score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
            return render_template("game.html",artist=random_artist,score=score)
    except:
        return apology('Timed out! please refresh this page')



@app.route('/my-link3/')
def my_link3():
    random_artist.clear() #when new round required, clear data of old round and choose new random artist
    return my_link2()

@app.route('/my-link4/')
def my_link4(): #when skip happen,loss 25 points and clear data about last round and choose new random artist
    score = db.execute("SELECT * FROM users WHERE id=? ", session["user_id"])[0]['score']
    total=score-25
    if total>0:
        db.execute("UPDATE users SET score = ? WHERE id = ?", total, session["user_id"])
    else:
        db.execute("UPDATE users SET score = ? WHERE id = ?", 0, session["user_id"])
    return my_link3()




@app.route("/new", methods=["GET", "POST"])
@login_required
def new(): #return new.html and deal with invalid inputs
    db.execute("UPDATE users SET score = ? WHERE id = ?", 0, session["user_id"])
    if request.method == "GET":
        artist=request.form.get("artist")
        if not artist:
            flash(f"please enter an artist name to start the game.")
            return render_template("new.html",fav_names=fav_names)
        if not valid_name(artist):
            flash(f"Sorry! but this artist in Unavailable")
            return render_template("new.html",fav_names=fav_names)
        fav_names.append(get_name(artist))
        fav_pics.append(get_pic(artist))
        return render_template("new.html",fav_names=fav_names)

    else:
        try:
            artist=request.form.get("artist")
            if not artist:
                flash(f"please enter an artist name to start the game.")
                return render_template("new.html",fav_names=fav_names)
            if not valid_name(artist):
                return apology("Sorry but this artist is not avilable")
            if artist in fav_names:
                flash(f"{artist} already exists!")
                return render_template("new.html",fav_names=fav_names)
            fav_names.append(get_name(artist))

            return render_template("new.html",fav_names=fav_names)
        except :
            return apology("Timed out. please try to refresh the page")


@app.route("/")
@login_required
def index(): #return index.html and clear any old data
        db.execute("UPDATE users SET score = ? WHERE id = ?", 0, session["user_id"])
        fav_names.clear()
        fav_pics.clear()
        appered.clear()
        random_artist.clear()
        name = db.execute("SELECT username FROM users WHERE id=? ", session["user_id"])[0]["username"]
        score = db.execute("SELECT high FROM users WHERE id=? ", session["user_id"])[0]["high"]
        return render_template("index.html", name=name, score=score)





@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")





@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "POST":
        if (
            request.form.get("username") == ""
            or request.form.get("password") == ""
            or request.form.get("confirmation") == ""
        ):
            return apology("username or password is empty.")
        elif (
            len(
                db.execute(
                    "SELECT * FROM users WHERE username = ?",
                    request.form.get("username"),
                )
            )
            > 0
        ):
            return apology("username already exists.")
        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("password do not match.")
        elif len(request.form.get("password")) < 4:
            return apology("password should be longer than 4 letters")
        pas = request.form.get("password")
        have_num = False
        have_symbol = False
        symbols = {
            "[",
            "@",
            "_",
            "!",
            "#",
            "$",
            "%",
            "^",
            "&",
            "*",
            "(",
            ")",
            "<",
            ">",
            "?",
            "/",
            "\\",
            "|",
            "}",
            "{",
            "~",
            ":",
            "]",
            "."
        }
        for letter in pas:
            if letter.isdigit():
                have_num = True
            if letter in symbols:
                have_symbol = True
        if not have_num or not have_symbol:
            return apology(
                "password should contain at least 1 digit and at least 1 special character"
            )
        db.execute(
            "INSERT INTO users (username, hash, score) VALUES(?, ?, ?)",
            request.form.get("username"),
            generate_password_hash(request.form.get("password")),
            0,
        )
        rows = db.execute(
            "SELECT * FROM users WHERE username = ?", request.form.get("username")
        )
        session["user_id"] = rows[0]["id"]
        return redirect("/")
    return render_template("register.html")

if __name__ =='__main__':
    app.run(debug=False,host='0.0.0.0')
