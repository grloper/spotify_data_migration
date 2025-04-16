import os
import logging
import json
import traceback
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from spotipy.exceptions import SpotifyException

logger = logging.getLogger(__name__)

class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.sp = None

    def authenticate(self):
        try:
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=self.client_id,
                client_secret=self.client_secret,
                redirect_uri=self.redirect_uri,
                scope="user-library-read user-library-modify playlist-read-private playlist-modify-private playlist-modify-public"
            ))
            logger.info("Authentication successful")
        except SpotifyException as e:
            logger.error(f"Spotify authentication failed: {e}")
            traceback.print_exc()

    def export_data(self, export_type, file_path, playlist_ids=None):
        try:
            if export_type == "liked_songs":
                results = self.sp.current_user_saved_tracks()
                songs = [{"name": item["track"]["name"], "artist": item["track"]["artists"][0]["name"]} for item in results["items"]]
                with open(file_path, "w") as f:
                    json.dump(songs, f)
                logger.info("Liked songs exported successfully")
            elif export_type == "playlists":
                playlists = []
                for playlist_id in playlist_ids:
                    playlist = self.sp.playlist(playlist_id)
                    playlists.append({
                        "name": playlist["name"],
                        "tracks": [{"name": track["track"]["name"], "artist": track["track"]["artists"][0]["name"]} for track in playlist["tracks"]["items"]]
                    })
                with open(file_path, "w") as f:
                    json.dump(playlists, f)
                logger.info("Playlists exported successfully")
        except SpotifyException as e:
            logger.error(f"Failed to export data: {e}")
            traceback.print_exc()

    def import_data(self, import_type, file_path, playlist_ids=None):
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            if import_type == "liked_songs":
                for song in data:
                    self.sp.current_user_saved_tracks_add([song["id"]])
                logger.info("Liked songs imported successfully")
            elif import_type == "playlists":
                for playlist in data:
                    new_playlist = self.sp.user_playlist_create(self.sp.me()["id"], playlist["name"], public=False)
                    self.sp.playlist_add_items(new_playlist["id"], [track["id"] for track in playlist["tracks"]])
                logger.info("Playlists imported successfully")
        except SpotifyException as e:
            logger.error(f"Failed to import data: {e}")
            traceback.print_exc()

    def erase_data(self, erase_type, playlist_ids=None):
        try:
            if erase_type == "liked_songs":
                results = self.sp.current_user_saved_tracks()
                song_ids = [item["track"]["id"] for item in results["items"]]
                self.sp.current_user_saved_tracks_delete(song_ids)
                logger.info("Liked songs erased successfully")
            elif erase_type == "playlists":
                for playlist_id in playlist_ids:
                    self.sp.user_playlist_unfollow(self.sp.me()["id"], playlist_id)
                logger.info("Playlists erased successfully")
        except SpotifyException as e:
            logger.error(f"Failed to erase data: {e}")
            traceback.print_exc()