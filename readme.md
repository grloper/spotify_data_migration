# Spotify Data Migration

A desktop application that allows you to export, import, and erase data from your Spotify account.

## Prerequisites

- Python 3.6 or higher
- Spotify account
- Spotify Developer account

## Installation

### Option 1: Standard Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/spotify_data_migration.git 
cd spotify_data_migration
```

2. Create and activate a virtual environment (recommended):
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install required dependencies:
```bash
pip install -r requirements.txt
```

### Option 2: Development Installation

If you plan to modify the code:

```bash
# After cloning and activating virtual environment
pip install -e .
```

## Getting Started

1. Create a Spotify Developer App:
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)
   - Log in with your Spotify account
   - Click "Create app"
   - Fill in the app name, description, and website
   - Add `http://localhost:8888/callback` as a redirect URI
   - Check the Developer Terms of Service and click "Create"
   - Note your Client ID and Client Secret from the app dashboard

2. Run the application:
```bash
# If using standard installation
python main.py

# If installed with pip
spotify-migrate
```

3. In the Setup tab:
   - Enter your Spotify Client ID, Client Secret, and Redirect URI
   - Click "Authenticate" to connect to your Spotify account
   - **Important**: Make sure the redirect URI matches exactly what's in your Spotify Dashboard
   - A browser window will open for you to log in to Spotify and authorize the application
   - After authorizing, you'll be redirected to the callback URL - this is normal!

## Usage

### Exporting Data
1. Go to the Export tab
2. Select what you want to export (playlists, liked songs)
3. Optionally select specific playlists
4. Choose a file to save the export
5. Click "Export Data"

### Importing Data
1. Go to the Import tab
2. Select what you want to import (playlists, liked songs)
3. Select the JSON file containing the export data
4. Optionally select specific playlists to import
5. Click "Import Data"

### Erasing Data
1. Go to the Erase tab
2. Select what you want to erase (playlists, liked songs)
3. Optionally select specific playlists to erase
4. Click "Erase Data"

## Troubleshooting

### Authentication Issues
- Make sure your Redirect URI exactly matches what's registered in the Spotify Developer Dashboard (including http:// prefix)
- Check that your Client ID and Client Secret are correct
- If you get errors after changing your credentials, try restarting the application

### Playlist Selection Problems
- If the playlist selection dialog shows no playlists, try authenticating again
- Check the log section at the bottom of the application for error messages
- If you have a large number of playlists, it may take some time to load them all

### Operation Failures
- Check the log section for detailed error information
- Ensure you have a stable internet connection
- For import/export operations, make sure you have appropriate file permissions

## Future Plans
- Integration with YouTube Music for cross-platform migration
- Playlist transfer by link
- Batch operations for multiple accounts

## License
This project is licensed under the MIT License - see the LICENSE file for details.