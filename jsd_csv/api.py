"""
JioSaavn API Client and Link Resolver.
Extracts metadata, lyrics, and direct CDN audio streams for songs, albums, playlists, and artists.
"""

import html
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Tuple

import requests

from .crypto import decrypt_saavn_url

logger = logging.getLogger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
}

API_BASE = "https://www.jiosaavn.com/api.php"


class JioSaavnAPI:
    """Official/Unofficial JioSaavn API client."""

    def __init__(self, session: Optional[requests.Session] = None):
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)

    def _call(self, params: Dict[str, Any]) -> Any:
        default_params = {
            "_format": "json",
            "_marker": "0",
            "ctx": "web6dot0",
            "api_version": "4",
        }
        merged = {**default_params, **params}
        try:
            resp = self.session.get(API_BASE, params=merged, timeout=15)
            resp.raise_for_status()
            text = resp.text.strip()
            # JioSaavn sometimes prefixes JSON with random comments or parentheses
            if text.startswith("/**/") or text.startswith("/*"):
                text = re.sub(r"^/\*\*?/?\s*", "", text)
            if not text:
                return {}
            return resp.json()
        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise

    def resolve_url(self, raw_input: str) -> Tuple[str, str]:
        """
        Parses an input URL or search query.
        Returns a tuple of (content_type, token_or_query).
        content_type can be: 'song', 'album', 'playlist', 'artist', or 'search'.
        """
        raw_input = raw_input.strip()

        # Follow redirects if it's a shortened link like saa.vn or jiosaavn.com/p/...
        if re.match(r"^https?://(saa\.vn|jiosaavn\.com/s/|jiosaavn\.com/p/)", raw_input, re.IGNORECASE):
            try:
                head_resp = self.session.head(raw_input, allow_redirects=True, timeout=10)
                raw_input = head_resp.url
            except Exception as e:
                logger.debug(f"Failed to follow redirect for {raw_input}: {e}")

        # If it doesn't look like a URL, treat it as a direct search query
        if not (raw_input.startswith("http://") or raw_input.startswith("https://")):
            return "search", raw_input

        parsed = urllib.parse.urlparse(raw_input)
        parts = [p for p in parsed.path.strip("/").split("/") if p]

        if not parts:
            return "search", raw_input

        # Check for song, album, playlist/featured, artist
        if "song" in parts:
            return "song", parts[-1]
        elif "album" in parts:
            return "album", parts[-1]
        elif "featured" in parts or "playlist" in parts:
            return "playlist", parts[-1]
        elif "artist" in parts:
            return "artist", parts[-1]

        # Fallback to last path segment as token, or search
        return "unknown", parts[-1]

    def upgrade_image_url(self, img_url: Optional[str]) -> str:
        """Upgrades album artwork URL from 150x150 or 50x50 to 500x500."""
        if not img_url:
            return ""
        # Replace dimensions with 500x500
        upgraded = re.sub(r"-\d+x\d+\.(jpg|jpeg|png)", r"-500x500.\1", img_url)
        upgraded = upgraded.replace("http://", "https://")
        return upgraded

    def format_song_item(self, raw: Dict[str, Any], track_idx: int = 1) -> Dict[str, Any]:
        """Normalizes raw JioSaavn song object into a rich, structured dictionary."""
        more_info = raw.get("more_info", {}) or {}

        # Extract artists: Cleanly separate essential musical performers from actors/starring cast
        artist_map = more_info.get("artistMap", {}) or {}
        primary_artists_list = artist_map.get("primary_artists", [])
        featured_artists_list = artist_map.get("featured_artists", [])

        unique_artists: List[str] = []
        seen_artists = set()

        def add_artist(name: str) -> None:
            if not name:
                return
            clean_name = html.unescape(name).strip()
            # If compound comma-separated string, process each individual artist
            for p in [x.strip() for x in clean_name.split(",") if x.strip()]:
                norm = p.lower()
                if norm not in seen_artists:
                    seen_artists.add(norm)
                    unique_artists.append(p)

        # 1. Primary musical artists
        for a in primary_artists_list:
            if isinstance(a, dict) and a.get("role") != "starring":
                add_artist(a.get("name", ""))

        # 2. Featured artists (singers, vocalists)
        for a in featured_artists_list:
            if isinstance(a, dict) and a.get("role") != "starring":
                add_artist(a.get("name", ""))

        # 3. Fallback: singers field in more_info
        if not unique_artists and more_info.get("singers"):
            add_artist(more_info.get("singers", ""))

        # 4. Fallback: artists list (excluding actors / starring cast)
        if not unique_artists:
            for a in artist_map.get("artists", []):
                if isinstance(a, dict) and a.get("role") not in ("starring", "actor"):
                    add_artist(a.get("name", ""))

        # 5. Fallback: music composer or subtitle
        if not unique_artists and more_info.get("music"):
            add_artist(more_info.get("music", ""))
        if not unique_artists and raw.get("subtitle"):
            add_artist(raw.get("subtitle", ""))

        essential_artists = ", ".join(unique_artists) if unique_artists else "Unknown Artist"
        primary_artist_str = unique_artists[0] if unique_artists else "Unknown Artist"

        # Album Artist: music composer for soundtracks (when matching primary artists), or primary musical artist
        raw_music = (more_info.get("music") or "").strip()
        album_artist = ""
        if raw_music and primary_artists_list:
            music_parts = [p.strip().lower() for p in raw_music.split(",") if p.strip()]
            for a in primary_artists_list:
                aname = html.unescape(a.get("name", "")).strip()
                if aname.lower() in music_parts or any(mp in aname.lower() for mp in music_parts):
                    album_artist = aname
                    break
        if not album_artist:
            album_artist = primary_artist_str

        # Clean title and album
        raw_title = raw.get("title") or raw.get("song") or "Unknown Title"
        title = html.unescape(raw_title).strip()
        raw_album = more_info.get("album") or raw.get("album") or "Unknown Album"
        album = html.unescape(raw_album).strip()

        # Duration
        try:
            duration_sec = int(more_info.get("duration") or raw.get("duration") or 0)
        except (ValueError, TypeError):
            duration_sec = 0
        dur_mins = duration_sec // 60
        dur_secs = duration_sec % 60
        duration_formatted = f"{dur_mins:02d}:{dur_secs:02d}"

        # Image
        img_url = self.upgrade_image_url(raw.get("image"))

        # Decrypt audio stream
        encrypted_media = more_info.get("encrypted_media_url") or raw.get("encrypted_media_url") or ""
        decrypted_url = decrypt_saavn_url(encrypted_media) if encrypted_media else ""

        # Build quality variants
        media_urls = {}
        if decrypted_url:
            for quality in ["320", "160", "96"]:
                media_urls[quality] = re.sub(r"_\d+\.mp4$", f"_{quality}.mp4", decrypted_url)

        # Year and release date
        year = raw.get("year") or more_info.get("release_date", "")[:4] or ""
        release_date = more_info.get("release_date") or ""

        # Lyrics info
        has_lyrics_str = str(more_info.get("has_lyrics", "false")).lower()
        has_lyrics = has_lyrics_str in ("true", "1")
        lyrics_id = more_info.get("lyrics_id") or raw.get("id") or ""
        lyrics_snippet = html.unescape(more_info.get("lyrics_snippet", "") or "")

        return {
            "id": raw.get("id", ""),
            "title": title,
            "artist": essential_artists,
            "artists": essential_artists,
            "primary_artists": primary_artist_str,
            "all_artists": essential_artists,
            "album_artist": album_artist,
            "album": album,
            "album_id": more_info.get("album_id", ""),
            "album_url": more_info.get("album_url", ""),
            "year": str(year),
            "release_date": release_date,
            "duration": duration_sec,
            "duration_formatted": duration_formatted,
            "language": raw.get("language", "").capitalize(),
            "label": html.unescape(more_info.get("label", "")),
            "copyright": html.unescape(more_info.get("copyright_text", "")),
            "perma_url": raw.get("perma_url", ""),
            "image": img_url,
            "has_lyrics": has_lyrics,
            "lyrics_id": lyrics_id,
            "lyrics_snippet": lyrics_snippet,
            "track_number": track_idx,
            "play_count": raw.get("play_count", ""),
            "explicit": bool(raw.get("explicit_content", False)),
            "encrypted_media_url": encrypted_media,
            "decrypted_media_url": decrypted_url,
            "media_urls": media_urls,
        }

    def get_lyrics(self, lyrics_id: str) -> str:
        """Fetches full lyrics for a track and returns cleaned plaintext."""
        if not lyrics_id:
            return ""
        try:
            res = self._call({
                "__call": "lyrics.getLyrics",
                "lyrics_id": lyrics_id,
            })
            raw_lyrics = res.get("lyrics", "")
            if not raw_lyrics:
                return ""
            # Convert <br> tags to newlines
            text = re.sub(r"<br\s*/?>", "\n", raw_lyrics)
            text = html.unescape(text).strip()
            return text
        except Exception as e:
            logger.debug(f"Failed to fetch lyrics for {lyrics_id}: {e}")
            return ""

    def get_song(self, token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetches a single song by its token."""
        res = self._call({
            "__call": "webapi.get",
            "token": token,
            "type": "song",
            "p": 1,
            "n": 20,
            "includeMetaTags": 0,
        })
        songs = res.get("songs", [])
        if not songs:
            # Try song.getDetails if token is numeric or pid
            res = self._call({
                "__call": "song.getDetails",
                "pids": token,
            })
            songs = res.get("songs", [])

        parsed = [self.format_song_item(s, idx + 1) for idx, s in enumerate(songs)]
        meta = {
            "type": "song",
            "title": parsed[0]["title"] if parsed else "Single",
            "artist": parsed[0]["primary_artists"] if parsed else "",
            "image": parsed[0]["image"] if parsed else "",
            "count": len(parsed),
        }
        return meta, parsed

    def get_album(self, token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetches an album and all its tracks."""
        res = self._call({
            "__call": "webapi.get",
            "token": token,
            "type": "album",
            "p": 1,
            "n": 100,
            "includeMetaTags": 0,
        })
        raw_songs = res.get("list", [])
        album_name = html.unescape(res.get("title", "Unknown Album"))
        primary_artist = html.unescape(res.get("primary_artists", ""))
        image = self.upgrade_image_url(res.get("image", ""))

        parsed = [self.format_song_item(s, idx + 1) for idx, s in enumerate(raw_songs)]
        if primary_artist:
            for s in parsed:
                if not s.get("album_artist") or s.get("album_artist") == "Unknown Artist":
                    s["album_artist"] = primary_artist
        meta = {
            "type": "album",
            "title": album_name,
            "artist": primary_artist,
            "year": res.get("year", ""),
            "image": image,
            "count": len(parsed),
            "perma_url": res.get("perma_url", ""),
        }
        return meta, parsed

    def get_playlist(self, token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetches a playlist and paginates to retrieve all tracks."""
        page = 1
        all_raw_songs: List[Dict[str, Any]] = []
        playlist_meta: Dict[str, Any] = {}

        while True:
            res = self._call({
                "__call": "webapi.get",
                "token": token,
                "type": "playlist",
                "p": page,
                "n": 50,
                "includeMetaTags": 0,
            })
            if page == 1:
                playlist_meta = {
                    "type": "playlist",
                    "title": html.unescape(res.get("title", "Playlist")),
                    "subtitle": html.unescape(res.get("subtitle", "")),
                    "image": self.upgrade_image_url(res.get("image", "")),
                    "perma_url": res.get("perma_url", ""),
                }

            page_songs = res.get("list", [])
            if not page_songs:
                break
            all_raw_songs.extend(page_songs)
            # If less than 50 songs returned, we've reached the end
            if len(page_songs) < 50:
                break
            page += 1

        parsed = [self.format_song_item(s, idx + 1) for idx, s in enumerate(all_raw_songs)]
        playlist_meta["count"] = len(parsed)
        return playlist_meta, parsed

    def get_artist(self, token: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Fetches an artist page and returns top songs."""
        # Search for artist first to get artist ID
        res = self._call({
            "__call": "search.getArtistResults",
            "q": token,
            "n": 5,
        })
        results = res.get("results", [])
        artist_id = token
        artist_name = token
        image = ""
        if results:
            artist_id = results[0].get("id", token)
            artist_name = results[0].get("name", token)
            image = self.upgrade_image_url(results[0].get("image"))

        details = self._call({
            "__call": "artist.getArtistPageDetails",
            "artistId": artist_id,
        })
        top_songs = details.get("topSongs", [])
        artist_name = html.unescape(details.get("name", artist_name))
        image = self.upgrade_image_url(details.get("image", image))

        parsed = [self.format_song_item(s, idx + 1) for idx, s in enumerate(top_songs)]
        meta = {
            "type": "artist",
            "title": f"{artist_name} - Top Songs",
            "artist": artist_name,
            "image": image,
            "count": len(parsed),
        }
        return meta, parsed

    def search_and_get(self, query: str, limit: int = 15) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Searches JioSaavn for songs matching query."""
        res = self._call({
            "__call": "search.getResults",
            "q": query,
            "n": limit,
        })
        results = res.get("results", [])
        parsed = [self.format_song_item(s, idx + 1) for idx, s in enumerate(results)]
        meta = {
            "type": "search",
            "title": f"Search: {query}",
            "artist": "",
            "image": parsed[0]["image"] if parsed else "",
            "count": len(parsed),
        }
        return meta, parsed

    def resolve_and_fetch(self, input_str: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Master resolver: Takes any JioSaavn link or search query,
        determines the type, and returns (collection_metadata, songs_list).
        """
        content_type, token = self.resolve_url(input_str)
        logger.info(f"Resolved input '{input_str}' -> type='{content_type}', token='{token}'")

        if content_type == "song":
            return self.get_song(token)
        elif content_type == "album":
            return self.get_album(token)
        elif content_type == "playlist":
            return self.get_playlist(token)
        elif content_type == "artist":
            return self.get_artist(token)
        elif content_type == "search":
            return self.search_and_get(token)
        else:
            # Attempt song -> album -> playlist -> search
            try:
                meta, songs = self.get_song(token)
                if songs:
                    return meta, songs
            except Exception:
                pass
            try:
                meta, songs = self.get_album(token)
                if songs:
                    return meta, songs
            except Exception:
                pass
            try:
                meta, songs = self.get_playlist(token)
                if songs:
                    return meta, songs
            except Exception:
                pass
            return self.search_and_get(token)
