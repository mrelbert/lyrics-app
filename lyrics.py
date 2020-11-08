import os
import sys
import json
import time
import signal
import spotipy
import threading
import webbrowser
import lyricsgenius as lg
import spotipy.util as util
from json.decoder import JSONDecodeError

def timed_input(prompt, timeout, timeoutmsg):
    def timeout_error(*_):
        raise TimeoutError
    signal.signal(signal.SIGALRM, timeout_error)
    signal.alarm(timeout)
    try:
        answer = input(prompt)
        signal.alarm(0)
        return answer
    except TimeoutError:
        if timeoutmsg:
            print(timeoutmsg)
        signal.signal(signal.SIGALRM, signal.SIG_IGN)
        return None

def sleeping(duration, result, index):
    time.sleep(duration)
    result[index] = True
    sys.exit()

# Scope required for currently playing
scope = "user-read-currently-playing"

# Create our spotifyOAuth object
spotifyOAuth = spotipy.SpotifyOAuth(client_id=os.environ['SPOTIPY_CLIENT_ID'],
                                    client_secret=os.environ['SPOTIPY_CLIENT_SECRET'],
                                    redirect_uri=os.environ['SPOTIPY_REDIRECT_URI'],
                                    scope=scope)

token = spotifyOAuth.get_access_token()
# print(json.dumps(token, sort_keys=True, indent=4))

# Create our spotifyObject
spotifyObject = spotipy.Spotify(auth=token['access_token'])

# Create out geniusObject
access_token = os.environ['GENIUS_ACCESS_TOKEN']
genius = lg.Genius(access_token)

counter = 1
result = [False]
index = 0

while True:

    print()
    print(">> updating current track [" + str(counter) + "]")
    print()
    counter += 1

    current = spotifyObject.currently_playing()
    current_type = current['currently_playing_type']

    if current_type == "track":

        artist = current['item']['artists'][0]['name']
        title = current['item']['name']
        length_ms = current['item']['duration_ms']
        progress_ms = current['progress_ms']
        time_ms = length_ms - progress_ms
        time_sec = int((time_ms/1000))
        # id = current['item']['id']
        search_query = artist + " " + title

        song = genius.search_song(title=title, artist=artist)
        # song = genius.search_songs(search_query)

        try:
            lyrics = song.lyrics
            url = song.url
            print()
            print(lyrics)
            print()
        except:
            print()
            print(">> lyrics were not found")
            print()

        # thread to track end of song without clogging main thread
        thread = threading.Thread(target=sleeping, args=(time_sec, result, index))
        thread.start()

        print(">> going to sleep for " + str(time_sec) + " seconds")
        print()
        print(">> enter 0 to open browser")
        print(">> enter 1 for artist info")
        print(">> enter nothing to continue")
        print(">> ctrl+c to exit")
        print()

        start = time.time()
        while result[index] == False:
            user_input = timed_input(">> ", time_sec, "moving on to the next track")
            if user_input == "0":
                print(">> updating browser with search query: \"{}\"".format(search_query))

                try:
                    webbrowser.open(url, new=0, autoraise=False)
                except:
                    print(">> could not find url")

            end = time.time()
            time_sec = time_sec - int(abs(start - end))

        # reset
        result[index] = False

    elif current_type == "ad":

        print(">> ad popped up -- sleeping...")
        time.sleep(30)

    # Check if access token has expired or not
    if spotifyOAuth.is_token_expired(token) == True:

        print(">> access token has expired -- refreshing...")

        token = spotifyOAuth.get_access_token()
        spotifyObject = spotipy.Spotify(auth=token['access_token'])
