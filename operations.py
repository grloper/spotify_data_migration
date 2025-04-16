import json
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

class SpotifyOperations:
    def __init__(self, spotify_client):
        self.spotify_client = spotify_client
    
    def export_data(self, export_playlists=True, export_liked_songs=True, selected_playlists=None, output_path=None):
        """Export data from Spotify to a JSON file."""
        if not self.spotify_client.sp:
            logger.error("Not authenticated with Spotify")
            return False
        
        data = {
            "user_id": self.spotify_client.user_id,
            "export_date": datetime.now().isoformat(),
            "playlists": [],
            "liked_songs": []
        }
        
        # Export playlists
        if export_playlists:
            playlists = self.spotify_client.get_playlists()
            
            for playlist in playlists:
                # Skip if not in selected playlists
                if selected_playlists and playlist['id'] not in selected_playlists:
                    continue
                    
                playlist_data = {
                    "id": playlist['id'],
                    "name": playlist['name'],
                    "description": playlist['description'],
                    "public": playlist['public'],
                    "tracks": []
                }
                
                tracks = self.spotify_client.get_playlist_tracks(playlist['id'])
                for track in tracks:
                    if track:
                        track_data = self._format_track_data(track)
                        playlist_data["tracks"].append(track_data)
                
                data["playlists"].append(playlist_data)
                logger.info(f"Exported playlist: {playlist['name']} with {len(playlist_data['tracks'])} tracks")
        
        # Export liked songs
        if export_liked_songs:
            liked_songs = self.spotify_client.get_liked_songs()
            for track in liked_songs:
                if track:
                    track_data = self._format_track_data(track)
                    data["liked_songs"].append(track_data)
            logger.info(f"Exported {len(data['liked_songs'])} liked songs")
        
        # Save to file
        if not output_path:
            output_path = f"spotify_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Data saved to {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving data to file: {str(e)}")
            return False
    
    def import_data(self, import_file, import_playlists=True, import_liked_songs=True, selected_playlists=None):
        """Import data to Spotify from a JSON file."""
        if not self.spotify_client.sp:
            logger.error("Not authenticated with Spotify")
            return False
        
        try:
            with open(import_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.info(f"Loaded data from {import_file}")
            
            # Import playlists
            if import_playlists and 'playlists' in data:
                for playlist_data in data['playlists']:
                    # Skip if not in selected playlists
                    if selected_playlists and playlist_data['id'] not in selected_playlists:
                        continue
                    
                    # Create new playlist
                    new_playlist = self.spotify_client.create_playlist(
                        name=playlist_data['name'],
                        public=playlist_data.get('public', False),
                        description=playlist_data.get('description', '')
                    )
                    
                    if new_playlist:
                        # Add tracks to playlist
                        track_uris = [track['uri'] for track in playlist_data['tracks'] if 'uri' in track]
                        if track_uris:
                            self.spotify_client.add_tracks_to_playlist(new_playlist['id'], track_uris)
                            logger.info(f"Added {len(track_uris)} tracks to playlist {playlist_data['name']}")
            
            # Import liked songs
            if import_liked_songs and 'liked_songs' in data:
                track_ids = [track['id'] for track in data['liked_songs'] if 'id' in track]
                if track_ids:
                    self.spotify_client.like_songs(track_ids)
                    logger.info(f"Imported {len(track_ids)} liked songs")
            
            return True
            
        except Exception as e:
            logger.error(f"Error importing data: {str(e)}")
            return False
    
    def erase_data(self, erase_playlists=True, erase_liked_songs=True, selected_playlists=None):
        """Erase data from Spotify."""
        if not self.spotify_client.sp:
            logger.error("Not authenticated with Spotify")
            return False
        
        try:
            # Erase playlists
            if erase_playlists:
                playlists = self.spotify_client.get_playlists()
                deleted_count = 0
                
                for playlist in playlists:
                    # Skip if not in selected playlists
                    if selected_playlists and playlist['id'] not in selected_playlists:
                        continue
                    
                    # Only delete playlists owned by the user
                    if playlist['owner']['id'] == self.spotify_client.user_id:
                        if self.spotify_client.delete_playlist(playlist['id']):
                            deleted_count += 1
                
                logger.info(f"Deleted {deleted_count} playlists")
            
            # Erase liked songs
            if erase_liked_songs:
                liked_songs = self.spotify_client.get_liked_songs()
                track_ids = [track['id'] for track in liked_songs if 'id' in track]
                
                if track_ids:
                    self.spotify_client.unlike_songs(track_ids)
                    logger.info(f"Unliked {len(track_ids)} songs")
            
            return True
            
        except Exception as e:
            logger.error(f"Error erasing data: {str(e)}")
            return False
    
    def _format_track_data(self, track):
        """Format track data for export."""
        artists = []
        if 'artists' in track:
            artists = [{'id': artist['id'], 'name': artist['name']} for artist in track['artists']]
        
        album = {}
        if 'album' in track:
            album = {
                'id': track['album']['id'],
                'name': track['album']['name']
            }
        
        return {
            'id': track['id'],
            'name': track['name'],
            'uri': track['uri'],
            'artists': artists,
            'album': album
        }
