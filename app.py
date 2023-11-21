import re
import requests
from dotenv import load_dotenv
from pytube import (YouTube, Search)
from datetime import timedelta
import os
import webbrowser

load_dotenv()

# READ ALL ENV VARIABLES FORM .env
CLIENT_ID = os.environ.get('CLIENT_ID')
CLIENT_SECRET = os.environ.get('CLIENT_SECRET')
RE_DIRECT_URL = os.environ.get('RE_DIRECT_URL')
API_URL = os.environ.get('API_URL')
PATH = os.environ.get('SONGS_LOCATION')


# GENERATE ACCESS TOKEN FROM SPOTIFY
def get_access_token():
    data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    response = requests.post(RE_DIRECT_URL, data=data)
    token_info = response.json()
    os.environ['ASSESS_TOKEN'] = token_info['access_token']
    os.environ['ASSESS_TOKEN_EXPIRE_TIME'] = str(token_info['expires_in'])
    return token_info


# SEARCH SONGS FROM YOUTUBE
def yt_search(list_of_song_names):
    for index, song in enumerate(list_of_song_names):
        song_name = f"{song['SONG NAME']} {song['ARTIST NAME']} {song['ALBUM NAME']}"
        s = Search(song_name)
        for i in s.results:
            yt = YouTube(i.watch_url)
            stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            if stream:
                stream.download(output_path=PATH, filename=sanitize_filename(i.title) + '.mp3')
                print(f"\"{song['SONG NAME']}\" downloaded successfully.!")
            break
    return "Songs Downloaded Successfully."


# SEARCH TRACK FROM SPOTIFY BASED ON TRACK OR PLAYLIST URL
def spotify_search(song_url: str):
    is_track = False
    is_playlist = False
    list_of_song_with_details = []
    if song_url == 'exit':
        exit()
    elif not song_url or not 'spotify.com/' in song_url:
        return "Please Enter Valid URL :( "

    # token_info = get_access_token()

    headers = {
        'Authorization': 'Bearer ' + os.environ.get('ASSESS_TOKEN'),
    }

    if 'track' in song_url:
        is_track = True
        end_point = f"tracks/{song_url.split('/track/')[1].split('?')[0]}"

    elif 'playlist' in song_url:
        end_point = f"playlists/{song_url.split('/playlist/')[1].split('?')[0]}/tracks"
        is_playlist = True
    else:
        print("INVALID URL")
        exit()
    response = requests.get(API_URL + end_point, headers=headers)
    if response.status_code == 401 or response.status_code == 400:
        get_access_token()
        requests.get(API_URL + end_point, headers=headers)
    elif response.status_code == 200:
        data = response.json()

        if is_track:
            artists_names = [i['name'] for i in data['artists']]
            sample = {
                "SONG NAME": data['name'],
                "ALBUM NAME": data['album']['name'],
                "ARTIST NAME": ','.join(artists_names),
                "SONG DURATION": milliseconds_to_min_int_str(int(data['duration_ms'])),
                "SONG RELEASE DATE": data['album']['release_date'],

            }
            list_of_song_with_details.append(sample)
        elif is_playlist:
            for i in data['items']:
                data = i['track']
                artists_names = [i['name'] for i in data['artists']]

                sample = {
                    "SONG NAME": data['name'],
                    "ALBUM NAME": data['album']['name'],
                    "ARTIST NAME": ','.join(artists_names),
                    "SONG DURATION": milliseconds_to_min_int_str(int(data['duration_ms'])),
                    "SONG RELEASE DATE": data['album']['release_date'],

                }
                list_of_song_with_details.append(sample)
        print(f"Total songs found on Spotify based on URL is {len(list_of_song_with_details)}")
        result = yt_search(list_of_song_with_details)
        return result
    else:
        return "ERROR"


# MILLISECONDS TO MIN:SEC FORMAT IN STR
def milliseconds_to_min_int_str(milliseconds: int):
    t = timedelta(milliseconds=milliseconds)
    minutes = t.seconds // 60
    seconds = t.seconds % 60
    return f"{minutes}:{seconds}"


# REMOVE SPECIAL CHARACTERS FROM SONG NAME FOUND ON YT
def sanitize_filename(title: str):
    sanitized_title = re.sub(r'[<>:"/\\|?*]', '', title)
    return sanitized_title


while True:
    print(f"\n--------- Type 'exit' for stop the process or you can close the window ---------")
    if not os.environ.get('ASSESS_TOKEN'):
        get_access_token()
    spotify_search(str(input('ENTER SPOTIFY SONG URL OR PLAYLIST URL : ')))
    webbrowser.open("file:///" + PATH.replace("\\", "/"))
