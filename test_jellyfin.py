#!/usr/bin/env python3
"""
Simple test script to verify Jellyfin API integration works with demo instance
"""

from playlist_migrator import JellyfinClient

def test_jellyfin_demo():
    """Test connecting to demo Jellyfin instance and searching for 'xd' playlist"""
    try:
        print("Testing Jellyfin API integration...")
        print("Connecting to demo.jellyfin.org/stable...")
        
        client = JellyfinClient('https://demo.jellyfin.org/stable', 'demo', '')
        
        print("Searching for 'xd' playlist...")
        playlists = client.search_playlists('xd')
        print(f'Found {len(playlists)} playlists matching "xd":')
        
        for p in playlists:
            print(f'  - {p["Name"]} (ID: {p["Id"]})')
            
            if p['Name'].lower() == 'xd':
                print(f"Getting items for playlist '{p['Name']}'...")
                items = client.get_playlist_items(p['Id'])
                print(f'    Playlist has {len(items)} items:')
                
                for i, item in enumerate(items[:5]):
                    name = item.get('Name', 'Unknown')
                    file_path = None
                    if "MediaSources" in item and item["MediaSources"]:
                        file_path = item["MediaSources"][0].get("Path", "No path")
                    print(f'      {i+1}. {name}')
                    if file_path:
                        print(f'         Path: {file_path}')
                
                if len(items) > 5:
                    print(f'      ... and {len(items) - 5} more items')
        
        print("\n✅ Jellyfin API integration test successful!")
        return True
        
    except Exception as e:
        print(f"\n❌ Jellyfin API integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_jellyfin_demo()
