#!/usr/bin/env python3
"""Make a TIDAL playlist from a playlists/*.txt file ("Artist - Title" per line).

Same TIDAL app and API as SCREENSHOT_TO_TIDAL (DJ Mantra, client id JjTAmDVohiV7GgOL,
OAuth 2.1 + PKCE, openapi.tidal.com v2). Standard library only.

    python3 tools/tidal_playlist.py login-url                 # prints a URL: open it, log in
    python3 tools/tidal_playlist.py login-finish '<URL>'      # the localhost URL the browser landed on
    python3 tools/tidal_playlist.py create playlists/X.txt [--name NAME] [--dry-run]
    python3 tools/tidal_playlist.py radio playlists/X.txt [--per N] [--name NAME] [--dry-run]
        # TIDAL's own continuation ("track radio") of each song in the file, mixed into one playlist

The token is kept outside the repository (~/.config/tidal_generated/token.json), or comes
from the TIDAL_REFRESH_TOKEN environment variable (a secret of the cloud environment).
"""
import base64, hashlib, json, os, re, secrets, sys, time, unicodedata
import urllib.error, urllib.parse, urllib.request

CLIENT_ID = os.environ.get("TIDAL_CLIENT_ID", "JjTAmDVohiV7GgOL")
REDIRECT = "http://localhost:8765/tidal-callback"
SCOPES = "user.read search.read playlists.read playlists.write"
LOGIN_URL = "https://login.tidal.com/authorize"
TOKEN_URL = "https://auth.tidal.com/v1/oauth2/token"
API = "https://openapi.tidal.com/v2"
STATE_DIR = os.path.expanduser("~/.config/tidal_generated")
TOKEN_FILE = os.path.join(STATE_DIR, "token.json")
PKCE_FILE = os.path.join(STATE_DIR, "pkce.json")
JSONAPI = "application/vnd.api+json"


def b64url(b):
    return base64.urlsafe_b64encode(b).decode().rstrip("=")


def save(path, obj):
    os.makedirs(STATE_DIR, exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)
    os.chmod(path, 0o600)


def load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return None


# --- auth

def token_request(fields):
    req = urllib.request.Request(TOKEN_URL, urllib.parse.urlencode(fields).encode(),
                                 {"Content-Type": "application/x-www-form-urlencoded"})
    try:
        with urllib.request.urlopen(req) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"TIDAL token error {e.code}: {e.read().decode()}")
    return {"access": j["access_token"], "refresh": j.get("refresh_token") or fields.get("refresh_token"),
            "expires": time.time() + float(j.get("expires_in", 3600)) - 60, "scope": j.get("scope", SCOPES)}


def login_url():
    verifier = b64url(secrets.token_bytes(48))
    state = b64url(secrets.token_bytes(16))
    save(PKCE_FILE, {"verifier": verifier, "state": state})
    q = {"response_type": "code", "client_id": CLIENT_ID, "redirect_uri": REDIRECT, "scope": SCOPES,
         "code_challenge_method": "S256", "code_challenge": b64url(hashlib.sha256(verifier.encode()).digest()),
         "state": state}
    print(LOGIN_URL + "?" + urllib.parse.urlencode(q))


def login_finish(landed):
    pk = load(PKCE_FILE) or sys.exit("run login-url first")
    q = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(landed.strip()).query))
    if "error" in q:
        sys.exit(f"TIDAL login: {q['error']} {q.get('error_description', '')}")
    if q.get("state") != pk["state"] or "code" not in q:
        sys.exit("TIDAL login: state mismatch or no code in that URL")
    t = token_request({"grant_type": "authorization_code", "client_id": CLIENT_ID, "code": q["code"],
                       "redirect_uri": REDIRECT, "code_verifier": pk["verifier"], "scope": SCOPES})
    save(TOKEN_FILE, t)
    os.remove(PKCE_FILE)
    print("logged in; scope:", t["scope"])


def access():
    t = load(TOKEN_FILE)
    if t and t["expires"] > time.time():
        return t["access"]
    refresh = (t or {}).get("refresh") or os.environ.get("TIDAL_REFRESH_TOKEN")
    if not refresh:
        sys.exit("not logged in: run login-url / login-finish, or set TIDAL_REFRESH_TOKEN")
    t = token_request({"grant_type": "refresh_token", "refresh_token": refresh, "client_id": CLIENT_ID})
    save(TOKEN_FILE, t)
    return t["access"]


# --- JSON:API

def call(method, path, params=None, body=None, retry=6, soft=False):
    url = API + path + ("?" + urllib.parse.urlencode(params) if params else "")
    req = urllib.request.Request(url, json.dumps(body).encode() if body is not None else None, method=method,
                                 headers={"Authorization": "Bearer " + access(), "Accept": JSONAPI,
                                          "Content-Type": JSONAPI})
    try:
        with urllib.request.urlopen(req) as r:
            d = r.read()
            return json.loads(d) if d else {}
    except urllib.error.HTTPError as e:
        if e.code == 429 and retry > 0:
            time.sleep(min(max(float(e.headers.get("Retry-After") or 2), (7 - retry) * 2), 60))
            return call(method, path, params, body, retry - 1, soft)
        if soft:
            return None
        sys.exit(f"TIDAL {method} {path} -> {e.code}: {e.read().decode()[:500]}")


def country():
    me = call("GET", "/users/me")
    return me.get("data", {}).get("attributes", {}).get("country") or "US"


def norm(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)|\[.*?\]|feat\..*|ft\..*", " ", s)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s).split())


def words(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return set(re.sub(r"[^a-z0-9]+", " ", s).split())


def sim(a, b):
    a, b = set(norm(a).split()), set(norm(b).split())
    return len(a & b) / max(len(a | b), 1)


VARIANT = re.compile(r"\b(remix|mix|mixed|live|edit|version|acoustic|instrumental|dub|karaoke|cover|rework|re-work|reprise|recut|demo|vip)\b", re.I)


def search_ids(q, cc):
    j = call("GET", "/searchResults/" + urllib.parse.quote(q, safe=""), {"countryCode": cc, "include": "tracks"},
             soft=True) or call("GET", "/searchResults", {"filter[query]": q, "countryCode": cc, "include": "tracks"})
    data = j.get("data") or {}
    if isinstance(data, list):
        data = data[0] if data else {}
    return [x["id"] for x in data.get("relationships", {}).get("tracks", {}).get("data", [])][:20]


def score(artist, title, name, version, arts):
    got = name + " " + (version or "")  # TIDAL keeps "Xyz Remix" in version
    s = 0.6 * sim(title, name) + 0.4 * max([sim(artist, a) for a in arts] or [0])
    if re.search(r"[(\[]", title):  # a named remix/version: its words count too
        s += 0.1 * len(words(title) & words(got)) / max(len(words(title) | words(got)), 1)
    if (version or re.search(r"[(\[]", name)) and not re.search(r"[(\[]", title):
        s -= 0.02  # any extra "(...)" or version nobody asked for: the plain one wins a tie
    if VARIANT.search(got) and not VARIANT.search(title):
        s -= 0.05  # prefer the original over remixes/live takes nobody asked for
    if re.search(r"\bmixed\b", got, re.I) and not re.search(r"\bmixed\b", title, re.I):
        s -= 0.05  # a cut from a continuous DJ mix
    return s


def queries(artist, title):
    """From exact to loose. The song matters more than the version: if the named remix isn't on TIDAL,
    the looser searches find the original or another version of the same song."""
    bare = norm(title)  # without "(... Remix)", "feat. ..."
    first = artist.split(",")[0].split("&")[0].strip()
    squashed = re.sub(r"[^\w\s]", "", re.sub(r"\(.*?\)|\[.*?\]", " ", title))  # "D.A.N.C.E." -> "DANCE"
    plain = re.sub(r"[()\[\]]", " ", title)
    qs = [f"{artist} {plain}", f"{artist} {bare}", f"{first} {bare}", f"{first} {squashed}", bare]
    out = []
    for q in qs:
        q = " ".join(q.split())
        if q and q.lower() not in map(str.lower, out):
            out.append(q)
    return out


def find(artist, title, cc):
    good = 1.1 if re.search(r"[(\[]", title) else 1.0  # a perfect match stops the search early
    best, best_score, seen = None, 0.0, set()
    for q in queries(artist, title):
        ids = [i for i in search_ids(q, cc) if i not in seen]
        seen.update(ids)
        if not ids:
            continue
        t = call("GET", "/tracks", {"filter[id]": ",".join(ids), "countryCode": cc, "include": "artists"})
        names = {i["id"]: i["attributes"]["name"] for i in t.get("included", []) if i["type"] == "artists"}
        rank = {i: n for n, i in enumerate(ids)}
        for tr in sorted(t.get("data", []), key=lambda x: rank.get(x["id"], 99)):
            arts = [names.get(a["id"], "") for a in tr.get("relationships", {}).get("artists", {}).get("data", [])]
            name, version = tr["attributes"]["title"], tr["attributes"].get("version")
            if sim(title, name) < 0.5 or max([sim(artist, a) for a in arts] or [0]) < 0.3:
                continue  # another song by the same artist, or the same title by someone else, is not the song
            s = score(artist, title, name, version, arts)
            if s > best_score:
                best, best_score = (tr["id"], ", ".join(arts), " - ".join(x for x in (name, version) if x)), s
        if best_score >= good - 1e-9:
            break
    return best, best_score


def read_list(path):
    rows, name = [], None
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if line.startswith("#") and name is None:
            name = line.lstrip("# ").strip()
        if not line or line.startswith("#"):
            continue
        pin = re.search(r"\s*\[tidal:(\d+)\]$", line)  # "Artist - Title [tidal:123]" pins an exact track
        if pin:
            line = line[:pin.start()]
        artist, _, title = line.partition(" - ")
        rows.append((artist.strip(), title.strip(), pin.group(1) if pin else None))
    return name, rows


def create(path, name=None, dry=False):
    first, rows = read_list(path)
    name = name or first or os.path.splitext(os.path.basename(path))[0]
    if "(generated)" not in name:
        name += " (generated)"
    cc = country()
    ids = []
    for artist, title, pin in rows:
        hit, s = ((pin, artist, title + " (pinned)"), 1.0) if pin else find(artist, title, cc)
        mark = "OK " if hit and s >= 0.6 else "-- "
        print(f"{mark}{s:4.0%}  {artist} - {title}" + (f"   => {hit[1]} - {hit[2]} [{hit[0]}]" if hit else ""))
        if hit and s >= 0.6 and hit[0] not in ids:
            ids.append(hit[0])
    print(f"\n{len(ids)}/{len(rows)} found")
    if dry:
        return
    made = call("POST", "/playlists", {"countryCode": cc}, {"data": {"type": "playlists", "attributes": {
        "name": name, "description": "Generated by Claude from playlists/" + os.path.basename(path),
        "accessType": "UNLISTED"}}})
    pid = made["data"]["id"]
    for i in range(0, len(ids), 20):
        call("POST", f"/playlists/{pid}/relationships/items", {"countryCode": cc},
             {"data": [{"type": "tracks", "id": x} for x in ids[i:i + 20]]})
    print(f"playlist '{name}': https://tidal.com/playlist/{pid}")


def pages(path, cc, limit=200):
    """Follow a relationship's page cursors; returns the related ids in order."""
    ids, nxt = [], path
    while nxt and len(ids) < limit:
        j = call("GET", nxt, None if "?" in nxt else {"countryCode": cc})
        ids += [x["id"] for x in j.get("data", [])]
        nxt = (j.get("links") or {}).get("next")
    return ids


def radio(path, name=None, dry=False, per=None):
    """The songs Marko picked, each followed by TIDAL's own continuation of it (its track radio),
    the way the app keeps playing after his choice. Duplicates are dropped."""
    first, rows = read_list(path)
    name = name or first or os.path.splitext(os.path.basename(path))[0]
    if "(generated)" not in name:
        name += " (generated)"
    cc = country()
    order, songs = [], set()
    for artist, title, pin in rows:
        hit, s = ((pin, artist, title), 1.0) if pin else find(artist, title, cc)
        if not hit or s < 0.6:
            print(f"--  {artist} - {title}: not found")
            continue
        mix = pages(f"/tracks/{hit[0]}/relationships/radio", cc)
        tracks = pages(f"/playlists/{mix[0]}/relationships/items", cc) if mix else []
        added = []
        seq = [hit[0]] + tracks[:per]
        for i in range(0, len(seq), 20):  # the same song can come as several releases: keep one
            batch = seq[i:i + 20]
            t = call("GET", "/tracks", {"filter[id]": ",".join(batch), "countryCode": cc, "include": "artists"})
            names = {x["id"]: x["attributes"]["name"] for x in t.get("included", []) if x["type"] == "artists"}
            got = {x["id"]: x for x in t.get("data", [])}
            for k in batch:
                x = got.get(k)
                if not x or k in order:
                    continue
                arts = [names.get(a["id"], "") for a in x["relationships"]["artists"]["data"]]
                key = (norm(arts[0] if arts else ""), norm(x["attributes"]["title"]), norm(x["attributes"].get("version") or ""))
                if key not in songs:
                    songs.add(key)
                    added.append(k)
        order += added
        print(f"OK  {artist} - {title}: +{len(added)} ({len(tracks)} in its radio)")
    print(f"\n{len(order)} songs")
    for i in range(0, min(len(order), 60), 20):  # show the start, so the mix can be checked
        t = call("GET", "/tracks", {"filter[id]": ",".join(order[i:i + 20]), "countryCode": cc, "include": "artists"})
        names = {x["id"]: x["attributes"]["name"] for x in t.get("included", []) if x["type"] == "artists"}
        got = {x["id"]: x for x in t.get("data", [])}
        for k in order[i:i + 20]:
            x = got.get(k)
            if x:
                arts = ", ".join(names.get(a["id"], "") for a in x["relationships"]["artists"]["data"])
                print(f"  {arts} - {x['attributes']['title']}")
    if dry:
        return
    made = call("POST", "/playlists", {"countryCode": cc}, {"data": {"type": "playlists", "attributes": {
        "name": name, "description": "TIDAL radio of the songs in playlists/" + os.path.basename(path)
                                     + ", generated by Claude", "accessType": "UNLISTED"}}})
    pid = made["data"]["id"]
    for i in range(0, len(order), 20):
        call("POST", f"/playlists/{pid}/relationships/items", {"countryCode": cc},
             {"data": [{"type": "tracks", "id": x} for x in order[i:i + 20]]})
    print(f"playlist '{name}': https://tidal.com/playlist/{pid}")


if __name__ == "__main__":
    a = sys.argv[1:]
    if a[:1] == ["login-url"]:
        login_url()
    elif a[:1] == ["login-finish"] and len(a) == 2:
        login_finish(a[1])
    elif a[:1] == ["create"] and len(a) >= 2:
        nm = a[a.index("--name") + 1] if "--name" in a else None
        create(a[1], nm, "--dry-run" in a)
    elif a[:1] == ["radio"] and len(a) >= 2:
        nm = a[a.index("--name") + 1] if "--name" in a else None
        per = int(a[a.index("--per") + 1]) if "--per" in a else None
        radio(a[1], nm, "--dry-run" in a, per)
    else:
        sys.exit(__doc__)
