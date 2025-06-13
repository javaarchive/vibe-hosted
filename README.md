# vibe-hosted

A partnership with AI for your selfhosted needs

## Jellyfin to Plex Playlist Migration Tool

This repository contains a CLI tool to migrate playlists from Jellyfin to Plex, assuming both services share identical container paths for media files.

### Features

- Migrate any Jellyfin playlist to Plex by name
- Automatic media file matching using identical container paths
- Dry-run mode to preview migrations without making changes
- Comprehensive error handling and logging
- Support for environment variables and command-line arguments
- Detailed progress reporting

### Installation

1. Clone this repository:
```bash
git clone https://github.com/javaarchive/vibe-hosted.git
cd vibe-hosted
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

### Authentication Setup

#### Jellyfin API Key
1. Log into your Jellyfin web interface
2. Go to Dashboard → API Keys
3. Create a new API key for the migration tool

#### Plex Username and Password
You will need your Plex account username and password. The tool will securely prompt for your password when you run it.

### Usage

#### Basic Usage
```bash
python migrate_playlist.py "My Playlist Name" \
  --jellyfin-url http://jellyfin:8096 \
  --jellyfin-api-key YOUR_JELLYFIN_API_KEY \
  --plex-url http://plex:32400 \
  --plex-username YOUR_PLEX_USERNAME
```
The tool will securely prompt for your Plex password.

#### Using Environment Variables
Set the following environment variables to avoid passing credentials on the command line:
```bash
export JELLYFIN_URL="http://jellyfin:8096"
export JELLYFIN_API_KEY="your_jellyfin_api_key"
export PLEX_URL="http://plex:32400"
export PLEX_USERNAME="your_plex_username"

python migrate_playlist.py "My Playlist Name"
```
The tool will still securely prompt for your Plex password.

#### Dry Run Mode
Preview what would be migrated without actually creating the playlist:
```bash
python migrate_playlist.py "My Playlist Name" --dry-run
```

#### Verbose Logging
Enable detailed logging for troubleshooting:
```bash
python migrate_playlist.py "My Playlist Name" --verbose
```

### Command Line Options

- `playlist_name` - Name of the playlist to migrate (required)
- `--jellyfin-url` - Jellyfin server URL
- `--jellyfin-api-key` - Jellyfin API key
- `--plex-url` - Plex server URL
- `--plex-username` - Plex username
- `--dry-run` - Preview migration without creating playlist
- `--verbose` - Enable verbose logging
- `--help` - Show help message

### Requirements

- Python 3.6+
- Both Jellyfin and Plex servers must be accessible
- Media files must have identical paths in both containers
- Valid API credentials for both services

### Troubleshooting

#### Authentication Errors
- Verify your Jellyfin API key is correct and has appropriate permissions
- Ensure your Plex username and password are correct
- Check that server URLs are accessible from where you're running the script

#### Missing Media Files
- The tool will report any media files that couldn't be found in Plex
- Ensure your media libraries are properly configured in both services
- Verify that file paths are identical between Jellyfin and Plex containers

#### Connection Issues
- Check that both servers are running and accessible
- Verify firewall settings allow connections to both services
- Use `--verbose` flag for detailed connection debugging

### License

This project is licensed under the GPL v3 License - see the LICENSE file for details.

