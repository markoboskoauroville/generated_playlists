# HANDOVER: generated_playlists

Updated 2026-10-16. Read this first in a new session; then wait for Marko's next reference song.

## What this repository is for

Marko (a DJ) sends reference songs, usually screenshots from his DJ app. Claude continues them into a playlist
in the same musical style, then:

1. writes `playlists/YYYY-MM-DD_<style>.txt`: one `Artist - Title` per line, first `#` line = playlist name;
2. creates the playlist on Marko's **TIDAL** account (his DJ app reads TIDAL), name ending in **(generated)**;
3. adds a row with the TIDAL link to the table in `README.md`, saves the reference screenshots in `handover/`,
   commits and pushes.

His rules so far:
- Put **(generated)** in every TIDAL playlist name, so he knows Claude made it.
- Include every song he sends, then continue in the same style up to the length he asks for (last one: 108).
- **The song matters, not the exact version.** If a named remix isn't on TIDAL, use the original or another
  version of the same song. Only swap for a different song when the song itself isn't there, and say so.
- A new reference in a new style becomes a **new** playlist (ask if it's unclear).

## Playlists made

| File | TIDAL | Songs | Notes |
|---|---|---|---|
| `2026-10-16_reggae-vocal-healing.txt` | [Reggae Vocal Healing (generated)](https://tidal.com/playlist/f819de05-39e0-4f6d-ab8e-c270e183d36d) | 36 | Reference: Nalini Blossom - The Water Blessing Song (`handover/reference_nalini-*.png`). Mike Love "Human Revolution" and Koffee "Toast" (only a remix) were swapped for "Love Will Find a Way" and "Raggamuffin". |
| `2026-10-16_nu-disco.txt` | [Nu Disco Chart (generated)](https://tidal.com/playlist/3fb44298-fa71-4bec-8016-eeda23e81105) | 108 | Reference: his DJ app's Nu Disco / Disco chart, #1-17 (`handover/reference_nu-disco-chart_*.png`), then nu disco, disco house, disco pop, classics. #18 was cut off in the screenshot and left out. On TIDAL, "Le Freak" is the original (the script now finds the Dimitri From Paris remix, so a rebuild would use it). |

Radio playlists (`radio` command): | `2026-10-17_celebration-radio.txt` | [Celebration Radio (generated)](https://tidal.com/playlist/4ce7e870-0cab-42c8-9ee8-42426b4c37cf) | 96 | TIDAL's continuation of Kool & The Gang - Celebration, which Marko liked. |
| `2026-10-17_70s-celebration.txt` | [70s - Celebration (generated)](https://tidal.com/playlist/c4a1b896-e432-4085-b78b-75e7fe39752c) | 110 (8.0 h) | The Celebration radio expanded to 8 hours: radios of 14 soul/funk/disco classics, mixed in turn, `--hours 8 --min-radios 2`. Marko dictated the name by voice ("17 aces minus celebration" = "70s - Celebration"). |

## The TIDAL tool: `tools/tidal_playlist.py` (stdlib only)

```
python3 tools/tidal_playlist.py login-url                    # prints a TIDAL login URL
python3 tools/tidal_playlist.py login-finish '<localhost URL>'
python3 tools/tidal_playlist.py create playlists/X.txt --dry-run   # check every match first
python3 tools/tidal_playlist.py create playlists/X.txt             # creates the playlist, prints its link
```

- Same TIDAL app and API as Marko's `markoboskoauroville/SCREENSHOT_TO_TIDAL`: the "DJ Mantra" app, client id
  `JjTAmDVohiV7GgOL` (public, no secret), OAuth 2.1 + PKCE, redirect `http://localhost:8765/tidal-callback`,
  API `https://openapi.tidal.com/v2`. Playlists are created `UNLISTED`; tracks are added 20 at a time.
- Token: `~/.config/tidal_generated/token.json` (never commit or print it), or the `TIDAL_REFRESH_TOKEN`
  environment variable. **`TIDAL_REFRESH_TOKEN` is set in Code_Space_108j** (tested 2026-10-16: it logs
  in, and TIDAL does not rotate it), so new sessions need no login. If it stops working (password change,
  "log out everywhere"), do the login below and ask Marko to replace the variable's value.
- `create` always makes a **new** playlist; it cannot edit an existing one.

**How matching works** (`find`): it tries searches from exact to loose (full line → title without the
"(... Remix)" → first artist only → title without punctuation, e.g. "D.A.N.C.E." → "DANCE" → title alone) and
stops at a perfect match. A candidate must match the title (≥ 50 % of words) **and** the artist, so another
song by the same artist, or a cover by someone else, is never taken. Among versions of the right song it
prefers, in order: the named remix if the line names one → the plain original → other versions. Remixes,
live, demo, reprise and "Mixed" (cuts from continuous DJ mixes) lose a tie. Lines scoring under 60 % are
reported with `--` and skipped.

**TIDAL's own continuation (`radio`):** TIDAL's API has no listening history, so the songs TIDAL autoplayed
after Marko's pick can't be read back. Instead, `radio` takes the songs he picked and, for each one, adds TIDAL's
**track radio** (`/tracks/{id}/relationships/radio` → a MIX playlist of about 100 songs, paged with cursors),
mixing the radios in turn (one song from each) and dropping repeats: the same song on another release, an edit,
a remaster or "The" in the artist name, and identical titles by another artist. `--per N` keeps the first N of
each radio, `--hours H` stops at that length (uses track durations), and `--min-radios 2` keeps only songs that
at least two radios agree on, which removes one-off picks outside the style. It's
the same algorithm the app uses to continue a song, but the exact order the app played can differ.

If search still can't reach a track, pin it: `Artist - Title [tidal:<track id>]` (used for "Lola's Theme (VIP)").

## Logging in (only if the token stops working; Marko is on an Android phone)

1. Run `login-url` and send Marko the URL. **All the steps must run in the same container**, because the PKCE
   verifier lives in `~/.config/tidal_generated/pkce.json`.
2. After he logs in, his browser shows **"Unable to connect / localhost"**. This is expected; the code is in the
   address. Because the page is in an in-app browser, the address is hidden: tell him to tap **⋮ → Copy link**
   (or "Open in browser" and copy the address bar) and paste the whole
   `http://localhost:8765/tidal-callback?code=...&state=...` back.
3. `login-finish '<that URL>'`. The scope it prints must include `playlists.write`.

## Environment

- Works in the **Code_Space_108j** environment (Custom network access with `login.tidal.com`,
  `auth.tidal.com`, `openapi.tidal.com`). In the account's Default environment the proxy refused TIDAL.
- Quick check: `for h in login.tidal.com auth.tidal.com openapi.tidal.com; do curl -s -o /dev/null -w "$h %{http_code}\n" https://$h/; done`.
  A 403 or 404 from CloudFront means the host is reachable. A refused CONNECT (403 from the proxy, no
  `server: CloudFront`) means it is blocked: tell Marko which host.

## Git

- Current work: branch `claude/generate-playlist-mpncvw` (contains everything). The older branch
  `ccr-bd69dadb-47iidg` holds the first session's work and the first handover, already merged here.
  No pull request has been opened.

## Open items

- "Apache": Marko mentioned a band with a name like that, singing about women healers, for the reggae style.
  Nobody has identified it yet. If you recognise it, offer to add 1-3 songs.
