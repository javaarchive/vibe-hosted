import argparse
import getpass
import os
import sys
from typing import List

import requests
from plexapi.server import PlexServer
from plexapi.myplex import MyPlexAccount


def get_jf_user(session: requests.Session, base_url: str) -> str:
    resp = session.get(f"{base_url.rstrip('/')}/Users/Me")
    resp.raise_for_status()
    return resp.json()["Id"]


def get_jf_playlists(session: requests.Session, base_url: str, user_id: str) -> List[dict]:
    params = {
        "IncludeItemTypes": "Playlist",
        "Recursive": "true",
        "userId": user_id,
    }
    resp = session.get(f"{base_url.rstrip('/')}/Items", params=params)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def get_jf_playlist_items(session: requests.Session, base_url: str, playlist_id: str, user_id: str) -> List[dict]:
    params = {"userId": user_id, "Fields": "Path"}
    resp = session.get(f"{base_url.rstrip('/')}/Playlists/{playlist_id}/Items", params=params)
    resp.raise_for_status()
    return resp.json().get("Items", [])


def find_plex_item(plex: PlexServer, path: str):
    for section in plex.library.sections():
        try:
            results = section.search(filename=path)
            if results:
                return results[0]
        except Exception:
            continue
    return None


def migrate_playlist(
    name: str,
    jf_url: str,
    jf_token: str,
    plex_url: str,
    plex_username: str,
    plex_password: str,
):
    session = requests.Session()
    session.headers["X-Emby-Token"] = jf_token
    user_id = get_jf_user(session, jf_url)

    playlists = get_jf_playlists(session, jf_url, user_id)
    playlist = next((p for p in playlists if p.get("Name") == name), None)
    if not playlist:
        raise SystemExit(f"Playlist '{name}' not found on Jellyfin")

    items = get_jf_playlist_items(session, jf_url, playlist["Id"], user_id)

    account = MyPlexAccount(plex_username, plex_password)
    plex = PlexServer(plex_url, account.authenticationToken)
    plex_items = []
    for item in items:
        path = item.get("Path")
        if not path:
            continue
        plex_item = find_plex_item(plex, path)
        if plex_item:
            plex_items.append(plex_item)
        else:
            print(f"Warning: could not find '{path}' in Plex", file=sys.stderr)

    if not plex_items:
        raise SystemExit("No matching items found in Plex")

    plex.createPlaylist(name, items=plex_items)
    print(f"Created playlist '{name}' in Plex with {len(plex_items)} items")


def main():
    parser = argparse.ArgumentParser(description="Migrate a Jellyfin playlist to Plex")
    parser.add_argument("playlist_name", help="Name of the Jellyfin playlist")
    parser.add_argument("--jellyfin-url", default=os.getenv("JELLYFIN_URL"))
    parser.add_argument("--jellyfin-token", default=os.getenv("JELLYFIN_API_KEY"))
    parser.add_argument("--plex-url", default=os.getenv("PLEX_URL"))
    parser.add_argument("--plex-username", default=os.getenv("PLEX_USERNAME"))
    parser.add_argument("--plex-password", default=os.getenv("PLEX_PASSWORD"))
    args = parser.parse_args()

    if not all([args.jellyfin_url, args.jellyfin_token, args.plex_url]):
        parser.error("Jellyfin and Plex connection information is required")

    if not args.plex_username:
        args.plex_username = input("Plex username: ")
    if not args.plex_password:
        args.plex_password = getpass.getpass("Plex password: ")

    migrate_playlist(
        args.playlist_name,
        args.jellyfin_url,
        args.jellyfin_token,
        args.plex_url,
        args.plex_username,
        args.plex_password,
    )


if __name__ == "__main__":
    main()
