#!/usr/bin/env python3
"""
Test script to verify the Jellyfin data display functionality works correctly
"""

from playlist_migrator import JellyfinClient

def test_jellyfin_data_display():
    """Test the detailed Jellyfin data display functionality"""
    try:
        print("Testing Jellyfin data display functionality...")
        print("Connecting to demo.jellyfin.org/stable...")
        
        client = JellyfinClient('https://demo.jellyfin.org/stable', 'demo', '')
        
        print("Searching for 'xd' playlist...")
        playlists = client.search_playlists('xd')
        
        if not playlists:
            print("No playlist found!")
            return False
        
        target_playlist = playlists[0]
        print(f"Found playlist: {target_playlist['Name']}")
        
        print("Retrieving playlist items...")
        jellyfin_items = client.get_playlist_items(target_playlist["Id"])
        
        if not jellyfin_items:
            print("Playlist is empty!")
            return False
        
        print(f"Found {len(jellyfin_items)} items in Jellyfin playlist")
        
        print("\n" + "="*60)
        print("JELLYFIN PLAYLIST DATA")
        print("="*60)
        print(f"Playlist Name: {target_playlist['Name']}")
        print(f"Playlist ID: {target_playlist['Id']}")
        print(f"Total Items: {len(jellyfin_items)}")
        print("\nPlaylist Items:")
        print("-" * 40)
        
        for i, item in enumerate(jellyfin_items, 1):
            print(f"\n{i}. {item.get('Name', 'Unknown Title')}")
            print(f"   Type: {item.get('Type', 'Unknown')}")
            print(f"   ID: {item.get('Id', 'Unknown')}")
            
            if "MediaSources" in item and item["MediaSources"]:
                media_source = item["MediaSources"][0]
                file_path = media_source.get("Path", "No path available")
                print(f"   File Path: {file_path}")
                
                if "Container" in media_source:
                    print(f"   Container: {media_source['Container']}")
                if "Size" in media_source:
                    size_mb = media_source["Size"] / (1024 * 1024)
                    print(f"   Size: {size_mb:.1f} MB")
            else:
                print("   File Path: No media sources available")
            
            if "RunTimeTicks" in item:
                runtime_seconds = item["RunTimeTicks"] / 10000000
                runtime_minutes = runtime_seconds / 60
                print(f"   Duration: {runtime_minutes:.1f} minutes")
            
            if "ProductionYear" in item:
                print(f"   Year: {item['ProductionYear']}")
            
            if "Artists" in item and item["Artists"]:
                artists = ", ".join(item["Artists"])
                print(f"   Artists: {artists}")
            
            if "Album" in item:
                print(f"   Album: {item['Album']}")
        
        print("\n" + "="*60)
        print("END JELLYFIN DATA DISPLAY TEST")
        print("="*60)
        
        print("\n✅ Jellyfin data display functionality test successful!")
        print("The CLI will show this detailed data before attempting Plex operations.")
        return True
        
    except Exception as e:
        print(f"\n❌ Jellyfin data display test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_jellyfin_data_display()
