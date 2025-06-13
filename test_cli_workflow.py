#!/usr/bin/env python3
"""
Test script to demonstrate the complete CLI workflow including new Plex browsing logic
"""

import subprocess
import sys

def test_cli_workflow():
    """Test the CLI with demo Jellyfin data to show the new Plex browsing approach"""
    try:
        print("Testing complete CLI workflow with demo Jellyfin instance...")
        print("This will show Jellyfin data retrieval and attempt Plex connection (which will fail but show debug output)")
        
        cmd = [
            "python3", "playlist_migrator.py",
            "--jellyfin-url", "https://demo.jellyfin.org/stable",
            "--jellyfin-username", "demo",
            "--jellyfin-password", "",
            "--plex-url", "http://localhost:32400", 
            "--plex-username", "dummy_user",
            "--plex-password", "dummy_password",
            "--playlist", "xd"
        ]
        
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        output, _ = process.communicate(input="n\n")
        
        print("CLI Output:")
        print("=" * 60)
        print(output)
        print("=" * 60)
        
        if "JELLYFIN PLAYLIST DATA" in output and "Migration cancelled by user" in output:
            print("\n✅ CLI workflow test successful!")
            print("- Jellyfin data display works correctly")
            print("- User confirmation prompt works")
            print("- Ready for user testing with real Plex credentials")
            return True
        else:
            print("\n❌ CLI workflow test failed - unexpected output")
            return False
            
    except Exception as e:
        print(f"\n❌ CLI workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_cli_workflow()
