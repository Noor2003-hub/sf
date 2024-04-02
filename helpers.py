'''import csv
from functools import wraps
import datetime
from flask import redirect, render_template, session
import requests
from spotifysearch.client import Client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials'''
import csv
#import discogs_client
from functools import wraps
import datetime
from flask import redirect, render_template, session
import requests
from spotifysearch.client import Client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from difflib import SequenceMatcher
cid = "6accb5d452554ee9af43586b7b95ab10"
secret = "64fe5f741b444062afdf0aa4d3db7b4c"
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp=spotipy.Spotify(client_credentials_manager=client_credentials_manager)



def get_song_date(song,artist): #get song date of release using song name and artist of it
    check=sp.search(song+'-'+artist,type='track')
    return check['tracks']['items'][0]['album']['release_date']


def get_song_pic(song,artist): #get the album pic using song name and artist of it
    check=sp.search(song+'-'+artist,type='track')
    return check['tracks']['items'][0]['album']['images'][0]['url']


def song_name(song, artist): #takes song name and artist, and figure out if this song is for this artist, then return the song name on spotify
    check=sp.search(song+'-'+artist,type='track')
    track_name= check['tracks']['items'][0]['name']
    i=0
    if '-' in track_name or '(' in track_name or '[' in track_name:
        for letter in track_name:
            if letter in ['-','(','[']:
                return (track_name[0:i])
                break
            i+=1
    return track_name

def song_artist(song): #get most match artist name using his song title
    check=sp.search(song,type='track')
    return check['tracks']['items'][0]['album']['artists'][0]['name']



def similar(a, b): #compare 2 strings if they are similar not equal
    return SequenceMatcher(None, a, b).ratio()



def get_pic(name): #get profile picture using artist name
    if name is None:
        return name
    check =sp.search(str(name), type='artist')
    image= check['artists']['items'][0]['images']
    return str(image[0]['url'])

#t="jxKlJKxMGltwDonuGzPigBjGpHcEvStESFPviiJy"
#d = discogs_client.Client('ExampleApplication/0.1', user_token=t)

def valid_name(name): #check if name exists in spotify artists
    if name is None:
        return True
    check=sp.search(str(name), type='artist')
    if not check:
        return False
    return True

def get_name(name): #return most match name of artist on spotify
    if name is None:
        return True
    check=sp.search(str(name), type='artist')
    artist_name= check['artists']['items'][0]['name']
    return artist_name




#token="BvOyeN9cef-yzRDZC7qPWnjY0xiSdo1ugewZR0VdWbWnbsHCWJZ8ERw7gzrr550m"




def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(url, cookies={"session": str(uuid.uuid4())}, headers={"User-Agent": "python-requests", "Accept": "*/*"})
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {
            "name": symbol,
            "price": price,
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"
