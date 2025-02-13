# Spotify Playlist & Liked Songs Export/Import Script

This script allows you to export your **Spotify playlists and liked songs** to a JSON file and later import them to another Spotify account.

## Prerequisites

1. **Create a Spotify Developer App**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Click **Create an App**
   - Set an app name and description
   - Copy the **Client ID** and **Client Secret** (you will use them in the `.env` file)
   - Under **Redirect URIs**, add `http://localhost:8080`
   - Click **Save**

2. **Install Required Python Packages**
   ```sh
   pip install -r requirements.txt
   ```

---

## Setup

### 1. Create a `.env` File

Create a `.env` file in the same directory as `app.py` and add the following:

```
CLIENT_ID='your_spotify_client_id'
CLIENT_SECRET='your_spotify_client_secret'
EXPORT_USERNAME='your_spotify_export_username'
IMPORT_USERNAME='your_spotify_import_username'
REDIRECT_URI='http://localhost:8080'
```

### How to Get These Values?
- **CLIENT_ID & CLIENT_SECRET**: Found in your **Spotify Developer Dashboard** under your created app.
- **EXPORT_USERNAME**: Your Spotify username (can be found in your Spotify profile or via [this guide](https://community.spotify.com/t5/FAQs/What-s-a-Spotify-username/ta-p/5286512)).
- **IMPORT_USERNAME**: The username of the account where you want to import the playlists and liked songs.
- **REDIRECT_URI**: Should be set to `http://localhost:8080` (same as added in the Spotify Developer settings).

---

## Usage

### Export Data
This will fetch all playlists and liked songs from the **exporting account** and save them to `spotify_data.json`.
```sh
python app.py --export
```

### Import Data
This will read `spotify_data.json` and add the playlists and liked songs to the **importing account**.
```sh
python app.py --import-data
```

---

## Additional Notes
- The script requires **authorization** when running for the first time.
- Make sure the Spotify Developer app is correctly set up with the required **scopes**.
- The export/import process may take a while depending on the number of playlists and songs.

---

## Installing Dependencies
Ensure you have the required dependencies installed using the `requirements.txt` file:
```sh
pip install -r requirements.txt
```

Contents of `requirements.txt`:
```
spotipy==2.23.0
python-dotenv==1.0.0
requests==2.31.0
```

---

### Troubleshooting
**403 Forbidden Error:**
- Ensure the Spotify Developer app has the correct **Redirect URI** set (`http://localhost:8080`).
- Make sure your **account is registered** as a user in the Developer Dashboard under "Users and Access."
- Delete the `.cache` file if the token is invalid and try again:
  ```sh
  rm -rf .cache
  ```

If you encounter issues, refer to the [Spotify Web API documentation](https://developer.spotify.com/documentation/web-api/) or open an issue in your project repository.

