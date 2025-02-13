import logging
import time
import os
import json
import spotipy
from dotenv import load_dotenv
from spotipy.oauth2 import SpotifyOAuth
from logging_config import log

load_dotenv()

SPOTIFY_SCOPE = 'playlist-modify-public playlist-modify-private user-library-read user-library-modify'

def auth(username, clean_cache=False):
    cache_path = f".cache-{username}"
    
    if clean_cache and os.path.exists(cache_path):
        log(f"Deleting cache file: {cache_path}", logging.INFO)
        os.remove(cache_path)

    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET'),
        redirect_uri=os.getenv('REDIRECT_URI'),
        scope=SPOTIFY_SCOPE,
        username=username  
    ))

def export_data(debug=False, clean_cache=False):
    start_time = time.time()
    sp = auth(os.getenv('EXPORT_USERNAME'), clean_cache)
    
    playlists = sp.current_user_playlists()
    playlist_data = []

    for playlist in playlists['items']:
        log(f"Fetching tracks for playlist: {playlist['name']} (ID: {playlist['id']})")
        
        tracks = []
        results = sp.playlist_tracks(playlist['id'])
        while results:
            tracks.extend([item['track']['uri'] for item in results['items'] if item['track']])
            results = sp.next(results) if results['next'] else None

        playlist_data.append({
            'id': playlist['id'],
            'name': playlist['name'],
            'public': playlist['public'],
            'tracks': tracks
        })

    liked_songs = []
    results = sp.current_user_saved_tracks()
    while results:
        liked_songs.extend([track['track']['uri'] for track in results['items'] if track['track']])
        results = sp.next(results) if results['next'] else None

    with open('spotify_data.json', 'w') as f:
        json.dump({'playlists': playlist_data, 'liked_songs': liked_songs}, f)

    log("Exported data to spotify_data.json")

    elapsed_time = time.time() - start_time
    log(f"export_data() completed in {elapsed_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)

def import_data(debug=False, clean_cache=False):
    start_time = time.time()
    sp = auth(os.getenv('IMPORT_USERNAME'), clean_cache)

    with open('spotify_data.json', 'r') as f:
        data = json.load(f)

    for i in range(0, len(data['liked_songs']), 50):
        sp.current_user_saved_tracks_add(data['liked_songs'][i:i+50])
    log("Imported liked songs")

    for playlist in data['playlists']:
        log(f"Creating playlist: {playlist['name']}")
        new_playlist = sp.user_playlist_create(sp.me()['id'], playlist['name'], public=playlist['public'])
        new_playlist_id = new_playlist['id']
        log(f"New playlist created with ID: {new_playlist_id}")

        track_uris = playlist['tracks']
        for i in range(0, len(track_uris), 100):
            sp.playlist_add_items(new_playlist_id, track_uris[i:i+100])

        log(f"Added {len(track_uris)} tracks to {playlist['name']}")

    log("Imported playlists from spotify_data.json")

    elapsed_time = time.time() - start_time
    log(f"import_data() completed in {elapsed_time:.2f} seconds", logging.DEBUG if debug else logging.INFO)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Export and import Spotify data')
    parser.add_argument('--export', action='store_true', help='Export data from Spotify')
    parser.add_argument('--import-data', action='store_true', help='Import data to Spotify')
    parser.add_argument('--debug', action='store_true', help='Enable debug logging')
    parser.add_argument('--clean-cache', action='store_true', help='Delete OAuth cache before running')

    args = parser.parse_args()

    if args.export:
        export_data(debug=args.debug, clean_cache=args.clean_cache)
    elif args.import_data:
        import_data(debug=args.debug, clean_cache=args.clean_cache)
