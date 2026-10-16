# generated_playlists

Playlists Claude generates from reference songs, to continue in the same musical style.

- `playlists/YYYY-MM-DD_<style>.txt`: one `Artist - Title` per line. The first `#` line is the playlist name.
  Every playlist made on TIDAL ends in **(generated)**.
- `tools/tidal_playlist.py`: puts a list on TIDAL (same DJ Mantra app and API as SCREENSHOT_TO_TIDAL).

```
python3 tools/tidal_playlist.py login-url                  # open it, log in to TIDAL
python3 tools/tidal_playlist.py login-finish '<the localhost URL the browser landed on>'
python3 tools/tidal_playlist.py create playlists/2026-10-16_reggae-vocal-healing.txt [--dry-run]
```

The cloud environment must allow `login.tidal.com`, `auth.tidal.com` and `openapi.tidal.com`.
The token stays out of the repo (`~/.config/tidal_generated/`), or comes from the `TIDAL_REFRESH_TOKEN` secret.

| Date | Playlist | Reference |
|---|---|---|
| 2026-10-16 | [Reggae Vocal Healing (generated)](https://tidal.com/playlist/f819de05-39e0-4f6d-ab8e-c270e183d36d) | Nalini Blossom - The Water Blessing Song |
