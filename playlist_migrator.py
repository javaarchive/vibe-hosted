#!/usr/bin/env python3
"""
Jellyfin to Plex Playlist Migration Tool

This CLI tool migrates playlists from Jellyfin to Plex, assuming both services
share identical container paths for media files.
"""

import argparse
import getpass
import json
import sys
from typing import Dict, List, Optional
from urllib.parse import urljoin

import requests
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount


class JellyfinClient:
    """Client for interacting with Jellyfin API"""
    
    def __init__(self, base_url: str, username: str, password: str):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.user_id = None
        self.access_token = None
        self._authenticate(username, password)
    
    def _authenticate(self, username: str, password: str):
        """Authenticate with Jellyfin server"""
        auth_url = f"{self.base_url}/Users/authenticatebyname"
        
        auth_data = {
            "Username": username,
            "Pw": password
        }
        
        headers = {
            "Content-Type": "application/json",
            "X-Emby-Authorization": 'MediaBrowser Client="playlist-migrator", Device="python-script", DeviceId="playlist-migrator-1", Version="1.0.0"'
        }
        
        try:
            response = self.session.post(auth_url, json=auth_data, headers=headers)
            response.raise_for_status()
            
            auth_result = response.json()
            self.user_id = auth_result["User"]["Id"]
            self.access_token = auth_result["AccessToken"]
            
            self.session.headers.update({
                "X-Emby-Authorization": f'MediaBrowser Client="playlist-migrator", Device="python-script", DeviceId="playlist-migrator-1", Version="1.0.0", Token="{self.access_token}"'
            })
            
            print(f"Successfully authenticated with Jellyfin as user: {auth_result['User']['Name']}")
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to authenticate with Jellyfin: {e}")
            sys.exit(1)
    
    def search_playlists(self, search_term: str) -> List[Dict]:
        """Search for playlists by name using user-specific endpoint"""
        search_url = f"{self.base_url}/Users/{self.user_id}/Items"
        
        params = {
            "searchTerm": search_term,
            "includeItemTypes": "Playlist",
            "recursive": True
        }
        
        try:
            response = self.session.get(search_url, params=params)
            response.raise_for_status()
            
            result = response.json()
            return result.get("Items", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to search playlists: {e}")
            return []
    
    def get_playlist_items(self, playlist_id: str) -> List[Dict]:
        """Get items in a playlist"""
        items_url = f"{self.base_url}/Playlists/{playlist_id}/Items"
        
        try:
            response = self.session.get(items_url)
            response.raise_for_status()
            
            result = response.json()
            return result.get("Items", [])
            
        except requests.exceptions.RequestException as e:
            print(f"Failed to get playlist items: {e}")
            return []


class PlexClient:
    """Client for interacting with Plex server"""
    
    def __init__(self, base_url: str, username: str, password: str, server_name: str = None):
        try:
            account = MyPlexAccount(username, password)
            print(f"Successfully authenticated with MyPlex as user: {account.username}")
            
            if server_name:
                self.server = account.resource(server_name).connect()
            else:
                token = account.authenticationToken
                self.server = PlexServer(base_url, token)
            
            print(f"Successfully connected to Plex server: {self.server.friendlyName}")
        except Exception as e:
            print(f"Failed to connect to Plex server: {e}")
            sys.exit(1)
    
    def find_media_by_path(self, file_path: str) -> Optional[object]:
        """Find media item in Plex by file path"""
        try:
            for library in self.server.library.sections():
                try:
                    results = library.search(filepath=file_path)
                    if results:
                        return results[0]
                except:
                    continue
            return None
        except Exception as e:
            print(f"Error searching for media by path {file_path}: {e}")
            return None
    
    def create_playlist(self, name: str, items: List[object]) -> bool:
        """Create a new playlist in Plex"""
        try:
            if not items:
                print(f"No valid items found to create playlist '{name}'")
                return False
            
            playlist = self.server.createPlaylist(name, items)
            print(f"Successfully created playlist '{name}' with {len(items)} items")
            return True
        except Exception as e:
            print(f"Failed to create playlist '{name}': {e}")
            return False


def migrate_playlist(jellyfin_url: str, jellyfin_username: str, jellyfin_password: str,
                    plex_url: str, plex_username: str, plex_password: str, playlist_name: str,
                    plex_server_name: str = None):
    """Main function to migrate a playlist from Jellyfin to Plex"""
    
    print(f"Starting migration of playlist '{playlist_name}'...")
    
    jellyfin = JellyfinClient(jellyfin_url, jellyfin_username, jellyfin_password)
    plex = PlexClient(plex_url, plex_username, plex_password, plex_server_name)
    
    print(f"Searching for playlist '{playlist_name}' in Jellyfin...")
    playlists = jellyfin.search_playlists(playlist_name)
    
    if not playlists:
        print(f"No playlist found with name '{playlist_name}'")
        return False
    
    target_playlist = None
    for playlist in playlists:
        if playlist["Name"].lower() == playlist_name.lower():
            target_playlist = playlist
            break
    
    if not target_playlist:
        target_playlist = playlists[0]
        print(f"Exact match not found, using playlist: {target_playlist['Name']}")
    else:
        print(f"Found playlist: {target_playlist['Name']}")
    
    print("Retrieving playlist items...")
    jellyfin_items = jellyfin.get_playlist_items(target_playlist["Id"])
    
    if not jellyfin_items:
        print("Playlist is empty or could not retrieve items")
        return False
    
    print(f"Found {len(jellyfin_items)} items in Jellyfin playlist")
    
    plex_items = []
    not_found_items = []
    
    for item in jellyfin_items:
        file_path = None
        if "MediaSources" in item and item["MediaSources"]:
            file_path = item["MediaSources"][0].get("Path")
        
        if not file_path:
            print(f"No file path found for item: {item.get('Name', 'Unknown')}")
            not_found_items.append(item.get('Name', 'Unknown'))
            continue
        
        plex_item = plex.find_media_by_path(file_path)
        
        if plex_item:
            plex_items.append(plex_item)
            print(f"✓ Found: {item.get('Name', 'Unknown')}")
        else:
            print(f"✗ Not found in Plex: {item.get('Name', 'Unknown')} (path: {file_path})")
            not_found_items.append(item.get('Name', 'Unknown'))
    
    if not plex_items:
        print("No matching items found in Plex. Cannot create playlist.")
        return False
    
    print(f"\nFound {len(plex_items)} matching items in Plex")
    if not_found_items:
        print(f"Could not find {len(not_found_items)} items in Plex:")
        for item_name in not_found_items:
            print(f"  - {item_name}")
    
    playlist_name_plex = f"{target_playlist['Name']} (from Jellyfin)"
    success = plex.create_playlist(playlist_name_plex, plex_items)
    
    if success:
        print(f"\n✅ Successfully migrated playlist '{playlist_name}' to Plex!")
        print(f"   Plex playlist name: '{playlist_name_plex}'")
        print(f"   Items migrated: {len(plex_items)}/{len(jellyfin_items)}")
        return True
    else:
        print(f"\n❌ Failed to create playlist in Plex")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Migrate playlists from Jellyfin to Plex",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python playlist_migrator.py --jellyfin-url https://demo.jellyfin.org/stable \\
                              --jellyfin-username demo \\
                              --plex-url http://localhost:32400 \\
                              --plex-username your_plex_user \\
                              --playlist "xd"
  
  python playlist_migrator.py --jellyfin-url https://your-jellyfin.com \\
                              --jellyfin-username your_user \\
                              --plex-url http://your-plex:32400 \\
                              --plex-username your_plex_user \\
                              --playlist "My Playlist"
        """
    )
    
    parser.add_argument("--jellyfin-url", required=True,
                       help="Jellyfin server URL (e.g., https://demo.jellyfin.org/stable)")
    parser.add_argument("--jellyfin-username", required=True,
                       help="Jellyfin username")
    parser.add_argument("--jellyfin-password",
                       help="Jellyfin password (will prompt if not provided)")
    parser.add_argument("--plex-url", required=True,
                       help="Plex server URL (e.g., http://localhost:32400)")
    parser.add_argument("--plex-username", required=True,
                       help="Plex username")
    parser.add_argument("--plex-password",
                       help="Plex password (will prompt if not provided)")
    parser.add_argument("--plex-server-name",
                       help="Plex server name (optional, for MyPlex users)")
    parser.add_argument("--playlist", required=True,
                       help="Name of the playlist to migrate")
    
    args = parser.parse_args()
    
    jellyfin_password = args.jellyfin_password
    if not jellyfin_password:
        jellyfin_password = getpass.getpass("Jellyfin password: ")
    
    plex_password = args.plex_password
    if not plex_password:
        plex_password = getpass.getpass("Plex password: ")
    
    success = migrate_playlist(
        args.jellyfin_url,
        args.jellyfin_username,
        jellyfin_password,
        args.plex_url,
        args.plex_username,
        plex_password,
        args.playlist,
        args.plex_server_name
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
