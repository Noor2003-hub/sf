# have get songs method only, becouse it couldnt work in helpers in the right way (i dont know why but i found test.py file is the solution)
from functools import wraps
from flask import redirect, render_template, session
from spotifysearch.client import Client
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

cid = "6accb5d452554ee9af43586b7b95ab10"
secret = "64fe5f741b444062afdf0aa4d3db7b4c"
client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp=spotipy.Spotify(client_credentials_manager=client_credentials_manager)

def get_songs(name): #get all songs title of single artist using there name
    if name is None:
        return name
    check =sp.search(str(name), type='artist')
    id= check['artists']['items'][0]['id']
    albums = sp.artist_albums(id)
    songs=[]
    for album in albums['items']:
        album_id = album['id']
        album_tracks = sp.album_tracks(album_id)
        for track in album_tracks['items']:
            track_name=track['name']
            name2=track_name
            i=0
            if '-' in track_name or '(' in track_name or '[' in track_name:
                for letter in track_name:
                    if letter in ['-','(','[']:
                        songs.append(track_name[0:i])
                        break
                    i+=1
            songs.append(track_name)
    return songs
