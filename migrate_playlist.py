#!/usr/bin/env python3

import argparse
import getpass
import json
import logging
import os
import sys
from typing import List, Dict, Optional, Any
from urllib.parse import urljoin

import requests
from plexapi.server import PlexServer
from plexapi.playlist import Playlist
from plexapi.myplex import MyPlexAccount
from plexapi.exceptions import NotFound, Unauthorized


class JellyfinClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'X-Emby-Token': api_key,
            'Content-Type': 'application/json'
        })

    def get_playlists(self) -> List[Dict[str, Any]]:
        url = urljoin(self.base_url, '/Playlists')
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('Items', [])

    def find_playlist_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        playlists = self.get_playlists()
        for playlist in playlists:
            if playlist.get('Name', '').lower() == name.lower():
                return playlist
        return None

    def get_playlist_items(self, playlist_id: str) -> List[Dict[str, Any]]:
        url = urljoin(self.base_url, f'/Playlists/{playlist_id}/Items')
        response = self.session.get(url)
        response.raise_for_status()
        return response.json().get('Items', [])


class PlexClient:
    def __init__(self, base_url: str, username: str, password: str):
        account = MyPlexAccount(username, password)
        self.plex = PlexServer(base_url, account.authToken)

    def find_media_by_path(self, file_path: str) -> Optional[Any]:
        for section in self.plex.library.sections():
            try:
                for item in section.all():
                    if hasattr(item, 'media'):
                        for media in item.media:
                            for part in media.parts:
                                if part.file == file_path:
                                    return item
            except Exception as e:
                logging.warning(f"Error searching section {section.title}: {e}")
                continue
        return None

    def create_playlist(self, name: str, items: List[Any]) -> Playlist:
        return Playlist.create(self.plex, name, items=items)

    def get_playlists(self) -> List[Playlist]:
        return self.plex.playlists()


class PlaylistMigrator:
    def __init__(self, jellyfin_client: JellyfinClient, plex_client: PlexClient):
        self.jellyfin = jellyfin_client
        self.plex = plex_client

    def migrate_playlist(self, playlist_name: str, dry_run: bool = False) -> bool:
        logging.info(f"Starting migration of playlist: {playlist_name}")
        
        jellyfin_playlist = self.jellyfin.find_playlist_by_name(playlist_name)
        if not jellyfin_playlist:
            logging.error(f"Playlist '{playlist_name}' not found in Jellyfin")
            return False

        logging.info(f"Found playlist: {jellyfin_playlist['Name']} (ID: {jellyfin_playlist['Id']})")
        
        jellyfin_items = self.jellyfin.get_playlist_items(jellyfin_playlist['Id'])
        logging.info(f"Playlist contains {len(jellyfin_items)} items")

        plex_items = []
        missing_items = []

        for item in jellyfin_items:
            item_name = item.get('Name', 'Unknown')
            logging.info(f"Processing item: {item_name}")
            
            file_path = None
            if 'MediaSources' in item and item['MediaSources']:
                media_source = item['MediaSources'][0]
                if 'Path' in media_source:
                    file_path = media_source['Path']
            
            if not file_path:
                logging.warning(f"No file path found for item: {item_name}")
                missing_items.append(item_name)
                continue

            plex_item = self.plex.find_media_by_path(file_path)
            if plex_item:
                plex_items.append(plex_item)
                logging.info(f"Found matching Plex item: {plex_item.title}")
            else:
                logging.warning(f"No matching Plex item found for path: {file_path}")
                missing_items.append(f"{item_name} ({file_path})")

        if missing_items:
            logging.warning(f"Could not find {len(missing_items)} items in Plex:")
            for item in missing_items:
                logging.warning(f"  - {item}")

        if not plex_items:
            logging.error("No matching items found in Plex. Cannot create playlist.")
            return False

        logging.info(f"Found {len(plex_items)} matching items in Plex")

        if dry_run:
            logging.info("DRY RUN: Would create playlist with the following items:")
            for item in plex_items:
                logging.info(f"  - {item.title}")
            return True

        try:
            new_playlist = self.plex.create_playlist(jellyfin_playlist['Name'], plex_items)
            logging.info(f"Successfully created playlist '{new_playlist.title}' in Plex")
            return True
        except Exception as e:
            logging.error(f"Failed to create playlist in Plex: {e}")
            return False


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )


def main():
    parser = argparse.ArgumentParser(
        description='Migrate a playlist from Jellyfin to Plex',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s "My Playlist" --jellyfin-url http://jellyfin:8096 --jellyfin-api-key YOUR_KEY --plex-url http://plex:32400 --plex-username YOUR_USERNAME
  %(prog)s "My Playlist" --dry-run
  %(prog)s "My Playlist" --verbose

Environment Variables:
  JELLYFIN_URL      Jellyfin server URL
  JELLYFIN_API_KEY  Jellyfin API key
  PLEX_URL          Plex server URL  
  PLEX_USERNAME     Plex username
        '''
    )
    
    parser.add_argument('playlist_name', help='Name of the playlist to migrate')
    parser.add_argument('--jellyfin-url', default=os.getenv('JELLYFIN_URL'),
                        help='Jellyfin server URL (default: JELLYFIN_URL env var)')
    parser.add_argument('--jellyfin-api-key', default=os.getenv('JELLYFIN_API_KEY'),
                        help='Jellyfin API key (default: JELLYFIN_API_KEY env var)')
    parser.add_argument('--plex-url', default=os.getenv('PLEX_URL'),
                        help='Plex server URL (default: PLEX_URL env var)')
    parser.add_argument('--plex-username', default=os.getenv('PLEX_USERNAME'),
                        help='Plex username (default: PLEX_USERNAME env var)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Preview what would be migrated without creating the playlist')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='Enable verbose logging')

    args = parser.parse_args()

    setup_logging(args.verbose)

    if not all([args.jellyfin_url, args.jellyfin_api_key, args.plex_url, args.plex_username]):
        logging.error("Missing required credentials. Please provide all of:")
        logging.error("  - Jellyfin URL and API key")
        logging.error("  - Plex URL and username")
        logging.error("Use --help for more information about setting these values.")
        sys.exit(1)

    plex_password = getpass.getpass("Enter Plex password: ")

    try:
        jellyfin_client = JellyfinClient(args.jellyfin_url, args.jellyfin_api_key)
        plex_client = PlexClient(args.plex_url, args.plex_username, plex_password)
        migrator = PlaylistMigrator(jellyfin_client, plex_client)
        
        success = migrator.migrate_playlist(args.playlist_name, args.dry_run)
        
        if success:
            if args.dry_run:
                logging.info("Dry run completed successfully")
            else:
                logging.info("Playlist migration completed successfully")
            sys.exit(0)
        else:
            logging.error("Playlist migration failed")
            sys.exit(1)
            
    except Unauthorized:
        logging.error("Authentication failed. Please check your credentials.")
        sys.exit(1)
    except requests.exceptions.ConnectionError:
        logging.error("Connection failed. Please check your server URLs.")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Unexpected error: {e}")
        if args.verbose:
            logging.exception("Full traceback:")
        sys.exit(1)


if __name__ == '__main__':
    main()
