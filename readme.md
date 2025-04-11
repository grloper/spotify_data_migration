# Spotify Playlist & Liked Songs Export/Import Script

This utility exports your **Spotify playlists and liked songs** to a JSON file and later imports them to another Spotify account. It is designed with modularity, error handling, and batch processing in mind for large collections.

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Setup](#setup)
  - [1. Create a .env File](#1-create-a-env-file)
- [Usage](#usage)
  - [Export Data](#export-data)
  - [Import Data](#import-data)
  - [Erase Data](#erase-data)
  - [Additional CLI Options](#additional-cli-options)
  - [Selective Operations](#selective-operations)
- [Project Architecture](#project-architecture)
  - [Key Components](#key-components)
- [⚠️Troubleshooting⚠️](#troubleshooting)
- [Installing Dependencies](#installing-dependencies)

---

## Prerequisites

1. **Create a Spotify Developer App**
   - Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
   - Click **Create an App**.
   - Set an app name and description.
   - Copy the **Client ID** and **Client Secret** (you will use these in the `.env` file).
   - Under **Redirect URIs**, add `http://127.0.0.1:8080`.
   - Click **Save**.
   - **IMPORTANT:** Ensure that the account you wish to use is added under **User Management** (see Troubleshooting).

2. **Install Required Python Packages**

   ```sh
   pip install -r requirements.txt
   ```

---

## Setup

### 1. Create a .env File

Create a `.env` file in the project root directory and add your Spotify API credentials.

#### Option 1: Different accounts for each operation

Use this configuration if you want to export from one account and import to another:

```env
CLIENT_ID='your_spotify_client_id'
CLIENT_SECRET='your_spotify_client_secret'
EXPORT_USERNAME='account_to_export_from'
IMPORT_USERNAME='account_to_import_to'
ERASE_USERNAME='account_to_erase_data_from'
REDIRECT_URI='http://127.0.0.1:8080'
```

#### Option 2: Same account for all operations

Use this simpler configuration if you're using the same Spotify account for all operations, or plan to manually change the account between runs.

```env
CLIENT_ID='your_spotify_client_id'
CLIENT_SECRET='your_spotify_client_secret'
SPOTIFY_USERNAME='your_spotify_username'
REDIRECT_URI='http://127.0.0.1:8080'
```

The script will use `SPOTIFY_USERNAME` as a fallback when operation-specific usernames aren't provided.

#### 🔍 Where to Get These Values?

- **CLIENT_ID** and **CLIENT_SECRET**  
  Obtain these from your [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/) under your created app.

- **EXPORT_USERNAME / IMPORT_USERNAME / ERASE_USERNAME**  
  These are your Spotify account usernames. Find them on your Spotify profile or review [this guide](https://community.spotify.com/t5/FAQs/What-s-a-Spotify-username/ta-p/5286512).

- **REDIRECT_URI**  
  This URI must match the one added in your Spotify app settings (typically: `http://127.0.0.1:8080`).

---

## Usage

Execute the script using the Python module flag (`-m`) followed by the package path (`src.main`) and your chosen action flag.

### Export Data

Fetch all playlists and liked songs from the **exporting account** (defined by `EXPORT_USERNAME` in `.env`) and save the data into `spotify_data.json` (or your specified file):

```sh
python -m src.main --export
```

### Import Data

Read the JSON file (defaults to `spotify_data.json`) and import the playlists and liked songs to the **importing account** (specified by `IMPORT_USERNAME` in `.env`):

```sh
python -m src.main --import-data
```

### Erase Data

**Warning:** This action will erase **all** playlists and liked songs from the **erasing account** (defined by `ERASE_USERNAME` in `.env`). A confirmation prompt will be displayed.

```sh
python -m src.main --erase
```

### Additional CLI Options

#### Enable Debug Mode

For detailed logging including API calls and timing, use the `--debug` flag:

```sh
python -m src.main --export --debug
```

#### Clear Cache Before Running

Using `--clean-cache` removes any cached authentication tokens before execution. This is useful when troubleshooting authentication issues or switching accounts:

```sh
python -m src.main --import-data --clean-cache
```

#### Specify Data File

You can define a custom JSON file for export/import with the `--data-file` flag:

```sh
python -m src.main --export --data-file my_backup.json
python -m src.main --import-data --data-file my_backup.json
```

#### Combined Usage Example

You may combine several options:

```sh
python -m src.main --export --debug --clean-cache --data-file custom_export.json 
```

This command:
- Clears the cached token for the `EXPORT_USERNAME`.
- Exports data to `custom_export.json`.
- Provides detailed debug logs.

### Selective Operations

You can use the `--selective` (or `-s`) flag to enable interactive selection of playlists for export, import, or deletion:

```sh
python -m src.main --export --selective
python -m src.main --import-data --selective
python -m src.main --erase --selective
```

This will present you with a list of available playlists and options to select specific ones:
- **Enter numbers separated by commas** (e.g., `1,3,5`)
- **Enter a range** (e.g., `1-5`)
- **Enter `all`** to select all playlists
- **Enter `public`** to select only public playlists
- **Enter `private`** to select only private playlists

For liked songs, you'll be prompted separately whether to include them in the operation.

Example:

```
Available Playlists:
------------------------------------------------------------
#    Playlist Name                          Track Count Public
------------------------------------------------------------
1    Workout Mix                            45         Yes
2    Chill Vibes                            120        No
3    Party Playlist                         85         Yes
...

Selection options:
- Enter numbers separated by commas (e.g., '1,3,5')
- Enter a range (e.g., '1-5')
- Enter 'all' to select all playlists
- Enter 'public' to select only public playlists
- Enter 'private' to select only private playlists
- Enter 'q' or press Ctrl+C to cancel

Select playlists: 1,3
```

---

## Project Architecture

The project is organized for modularity and ease of maintenance:

```
spotify_data_migration/
├── src/
│   ├── __init__.py
│   ├── config.py         # Loads configuration & environment variables
│   ├── spotify_manager.py # Core interactions with the Spotify API, including:
│   │                     #  - Authentication
│   │                     #  - Playlist and track operations (with automatic pagination)
│   │                     #  - Rate limiting and error handling
│   ├── data_handler.py   # JSON operations for export/import
│   ├── logger.py         # Logging configuration and setup
│   └── main.py           # CLI and main execution logic
├── .env                  # Environment variable configuration
├── requirements.txt      # Project dependencies
└── README.md             # Documentation (this file)
```

### Key Components

- **SpotifyManager:**  
  Contains methods for authenticating, fetching playlists & liked songs, handling paginated API responses, and managing rate limits (e.g., automatic retries with exponential backoff).

- **Data Handler:**  
  Provides robust functions to export data to a JSON file and import data from it, ensuring data integrity and proper error handling during file operations.

- **Logger:**  
  Configured for both human-readable logs and optional JSON-formatted logs for integration with monitoring tools.

- **CLI (main.py):**  
  Parses command-line arguments and orchestrates the overall export/import/erase operations, with user confirmations for critical operations.



## ⚠️Troubleshooting⚠️

### **403 Forbidden Error**

- Verify that your Spotify Developer app has the correct **Redirect URI** (`http://127.0.0.1:8080`).
- Ensure the target Spotify account is registered as a user in your Spotify app settings.
- Remove cached tokens by deleting any `.cache*` files:

  ```sh
  rm -rf .cache*
  ```

### **User Not Registered Error**

If you see the error message below:

```
Check settings on developer.spotify.com/dashboard, the user may not be registered., reason: None
```

Complete these steps to register the user:

1. Visit the [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/).
2. Open your Spotify App.
3. Go to **Edit Settings** → **User Management**.
4. Add the user in the `username:email` format, for example:

   ```
   myspotifyusername:myemail@example.com
   ```

5. Click **Save** and try running the script again.

For further details, refer to the [Spotify Web API Documentation](https://developer.spotify.com/documentation/web-api/).



## Installing Dependencies

Ensure that all required dependencies are installed using the provided `requirements.txt`:

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

Feel free to contribute improvements or report issues by opening an issue in the project repository. Enjoy backing up and migrating your Spotify data with confidence!


