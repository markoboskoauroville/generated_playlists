# generated_playlists

Playlists Claude generates from reference songs, to continue in the same musical style.

- `playlists/YYYY-MM-DD_<style>.txt`: one `Artist - Title` per line. The first `#` line is the playlist name.
  Add `[tidal:<id>]` at the end of a line to pin an exact TIDAL track when search can't find it.
  Every playlist made on TIDAL ends in **(generated)**.
- `tools/tidal_playlist.py`: puts a list on TIDAL (same DJ Mantra app and API as SCREENSHOT_TO_TIDAL).

```
python3 tools/tidal_playlist.py login-url                  # open it, log in to TIDAL
python3 tools/tidal_playlist.py login-finish '<the localhost URL the browser landed on>'
python3 tools/tidal_playlist.py create playlists/2026-10-16_reggae-vocal-healing.txt [--dry-run]
python3 tools/tidal_playlist.py radio playlists/X.txt [--per N] [--dry-run]   # TIDAL's own continuation of each song
```

The cloud environment must allow `login.tidal.com`, `auth.tidal.com` and `openapi.tidal.com`.
The token stays out of the repo (`~/.config/tidal_generated/`), or comes from the `TIDAL_REFRESH_TOKEN` secret.

| Date | Playlist | Reference |
|---|---|---|
| 2026-10-16 | [Reggae Vocal Healing (generated)](https://tidal.com/playlist/f819de05-39e0-4f6d-ab8e-c270e183d36d) | Nalini Blossom - The Water Blessing Song |
| 2026-10-16 | [Nu Disco Chart (generated)](https://tidal.com/playlist/3fb44298-fa71-4bec-8016-eeda23e81105) | Nu Disco / Disco chart, top 17 (DJ app screenshots) |
| 2026-10-17 | [Celebration Radio (generated)](https://tidal.com/playlist/4ce7e870-0cab-42c8-9ee8-42426b4c37cf) | TIDAL radio of Kool & The Gang - Celebration (96 songs) |
| 2026-10-17 | [70s, 80s - Celebration (generated)](https://tidal.com/playlist/c4a1b896-e432-4085-b78b-75e7fe39752c) | 8 h of TIDAL radio from 14 soul, funk and disco classics, led by Celebration (110 songs) |
