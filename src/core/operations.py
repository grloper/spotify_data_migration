import json
import logging
import os
from datetime import datetime

from src.core.spotify_client import SpotifyClient

logger = logging.getLogger(__name__)

class SpotifyOperations:
    def __init__(self, client: SpotifyClient):
        self.client = client

    def export_data(self, export_type: str, file_path: str, playlist_ids=None):
        try:
            data = {}
            if export_type == "playlists":
                data = self.client.get_playlists(playlist_ids)
            elif export_type == "liked_songs":
                data = self.client.get_liked_songs()

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            logger.info(f"Data exported successfully to {file_path}")
        except Exception as e:
            logger.error(f"Failed to export data: {e}")

    def import_data(self, import_type: str, file_path: str, playlist_ids=None):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            if import_type == "playlists":
                self.client.add_playlists(data, playlist_ids)
            elif import_type == "liked_songs":
                self.client.add_liked_songs(data)

            logger.info(f"Data imported successfully from {file_path}")
        except Exception as e:
            logger.error(f"Failed to import data: {e}")

    def erase_data(self, erase_type: str, playlist_ids=None):
        try:
            if erase_type == "playlists":
                self.client.delete_playlists(playlist_ids)
            elif erase_type == "liked_songs":
                self.client.delete_liked_songs()

            logger.info(f"Data erased successfully")
        except Exception as e:
            logger.error(f"Failed to erase data: {e}")