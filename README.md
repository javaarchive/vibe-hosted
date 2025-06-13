# vibe-hosted

a partnership with Codex for your selfhosted needs

## Playlist migration

Install dependencies:

```bash
pip install -r requirements.txt
```

Usage:

```bash
python -m migrate_playlist.cli "My Playlist" \
  --jellyfin-url http://jellyfin:8096 \
  --jellyfin-token YOUR_JELLYFIN_API_KEY \
  --plex-url http://plex:32400
```

The CLI will prompt for your Plex username and password if not provided. You may
also supply them as `--plex-username` and `--plex-password` options or the
environment variables `PLEX_USERNAME` and `PLEX_PASSWORD`.

Environment variables `JELLYFIN_URL`, `JELLYFIN_API_KEY` and `PLEX_URL` may be
used in place of command line options.
