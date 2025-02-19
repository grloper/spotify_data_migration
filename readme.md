# Spotify Playlist & Liked Songs Export/Import Script

This script allows you to export your **Spotify playlists and liked songs** to a JSON file and later import them to another Spotify account.

## Prerequisites

1. **Create a Spotify Developer App**
   - Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Click **Create an App**
   - Set an app name and description
   - Copy the **Client ID** and **Client Secret** (you will use them in the .env file)
   - Under **Redirect URIs**, add http://localhost:8080
   - Click **Save**
   - **IMPORTANT:** Ensure that the user is registered under **User Management** (see Troubleshooting section below).

2. **Install Required Python Packages**

   ```sh
   pip install -r requirements.txt
   ```

---

## Setup

### 1. Create a .env File

Create a .env file in the same directory as app.py and add the following:

```
CLIENT_ID='your_spotify_client_id'
CLIENT_SECRET='your_spotify_client_secret'
EXPORT_USERNAME='your_spotify_export_username'
IMPORT_USERNAME='your_spotify_import_username'
REDIRECT_URI='http://localhost:8080'
ERASE_USERNAME='your_spotify_erase_username'
```

### How to Get These Values?
- **CLIENT_ID & CLIENT_SECRET**: Found in your **Spotify Developer Dashboard** under your created app.
- **EXPORT_USERNAME**: Your Spotify username (can be found in your Spotify profile or via [this guide](https://community.spotify.com/t5/FAQs/What-s-a-Spotify-username/ta-p/5286512)).
- **IMPORT_USERNAME**: The username of the account where you want to import the playlists and liked songs.
- **REDIRECT_URI**: Should be set to http://localhost:8080 (same as added in the Spotify Developer settings).
- **ERASE_USERNAME**: The username of the account from which you want to erase playlists and liked songs.

---

## Usage

### Export Data
This will fetch all playlists and liked songs from the **exporting account** and save them to spotify_data.json.

```sh
python app.py --export
```

### Import Data
This will read spotify_data.json and add the playlists and liked songs to the **importing account**.

```sh
python app.py --import-data
```

### Erase Data
This will erase playlists and liked songs from the **erasing account** specified in `.env`.

```sh
python app.py --erase
```

### Enable Debug Mode
Use --debug to get detailed logging and execution time information.

```sh
python app.py --export --debug
```

### Clear Cache Before Running (**Recommended**)
Using **--clean-cache** will remove the cached authentication token before execution, ensuring the script runs smoothly without outdated credentials.

```sh
python app.py --import-data --clean-cache
```

### Combined Usage Example
You can use multiple flags together:

```sh
python app.py --export --debug --clean-cache
```

This will:
- Remove the cached authentication token (**recommended**)
- Export data
- Provide detailed debug logs

---

## Additional Notes
- The script requires **authorization** when running for the first time.
- Make sure the Spotify Developer app is correctly set up with the required **scopes**.
- The export/import process may take a while depending on the number of playlists and songs.

---

## Installing Dependencies
Ensure you have the required dependencies installed using the requirements.txt file:

```sh
pip install -r requirements.txt
```

Contents of requirements.txt:

```
spotipy==2.23.0
python-dotenv==1.0.0
requests==2.31.0
```

---

### Troubleshooting

#### **403 Forbidden Error**:
- Ensure the Spotify Developer app has the correct **Redirect URI** set (http://localhost:8080).
- Make sure your **account is registered** as a user in the Developer Dashboard under "Users and Access."
- Delete the .cache file if the token is invalid and try again:

  ```sh
  rm -rf .cache*
  ```

#### **User Not Registered Error**:
If you encounter an error like:

```
Check settings on developer.spotify.com/dashboard, the user may not be registered., reason: None
```

You need to **register the user in the Spotify Developer App**:

1. Go to the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Open your **Spotify App**.
3. Navigate to **Edit Settings** → **User Management**.
4. Add the user in the following **key-value format**:
   
   ```
   username:email
   ```
   
   Example:
   ```
   myspotifyusername:myemail@example.com
   ```
5. Click **Save**.

After completing these steps, try running the script again.

If you encounter further issues, refer to the [Spotify Web API documentation](https://developer.spotify.com/documentation/web-api/) or open an issue in your project repository.
