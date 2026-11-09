"""
YouTube Music exact matcher and yt-dlp downloader.
Finds exact matches on YouTube Music based on title, artist, album, and duration,
and downloads the audio stream when JioSaavn direct download is unavailable or bypassed.
"""

import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import yt_dlp
from ytmusicapi import YTMusic

try:
    from rapidfuzz import fuzz
    def _string_similarity(a: str, b: str) -> float:
        return fuzz.token_set_ratio(a, b) / 100.0
except ImportError:
    import difflib
    def _string_similarity(a: str, b: str) -> float:
        return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()

logger = logging.getLogger(__name__)


def clean_title_for_search(title: str) -> str:
    """Removes extra fluff from titles like (From "Movie"), (Feat. ...), (Lofi...), etc."""
    cleaned = re.sub(r"\((from\s+[\"'].*?[\"']|feat\..*?|with\s+.*?|official.*?)\)", "", title, flags=re.IGNORECASE)
    cleaned = re.sub(r"\[.*?\]", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or title


def parse_duration_to_seconds(dur_str: str) -> int:
    """Parses 'MM:SS' or 'H:MM:SS' into integer seconds."""
    if not dur_str or not isinstance(dur_str, str):
        return 0
    parts = dur_str.strip().split(":")
    try:
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        elif len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
    except (ValueError, TypeError):
        pass
    return 0


class YTMusicMatcher:
    """Finds exact track matches on YouTube Music with confidence scoring."""

    def __init__(self, cookies_file: Optional[str] = None):
        self.cookies_file = cookies_file if (cookies_file and os.path.exists(cookies_file)) else None
        try:
            self.ytm = YTMusic()
        except Exception as e:
            logger.warning(f"Could not initialize YTMusic client: {e}")
            self.ytm = None

    def search_exact_match(
        self,
        song_metadata: Dict[str, Any],
        tolerance_seconds: int = 25
    ) -> Optional[Dict[str, Any]]:
        """
        Searches YouTube Music for the exact match of the given JioSaavn song metadata.
        Returns match dictionary with videoId, url, title, duration, and match_score.
        """
        title = song_metadata.get("title", "")
        primary_artist = song_metadata.get("primary_artists", "") or song_metadata.get("artist", "")
        album = song_metadata.get("album", "")
        target_duration = int(song_metadata.get("duration") or 0)

        cleaned_title = clean_title_for_search(title)
        query = f"{cleaned_title} {primary_artist}".strip()

        candidates: List[Dict[str, Any]] = []

        # 1. Search via ytmusicapi
        if self.ytm:
            try:
                raw_results = self.ytm.search(query, filter="songs")
                for r in raw_results:
                    video_id = r.get("videoId")
                    if not video_id:
                        continue
                    cand_title = r.get("title", "")
                    cand_artists = ", ".join(a.get("name", "") for a in r.get("artists", []))
                    cand_album = r.get("album", {}).get("name", "") if r.get("album") else ""
                    cand_dur_str = r.get("duration", "0:00")
                    cand_dur_sec = parse_duration_to_seconds(cand_dur_str)

                    candidates.append({
                        "video_id": video_id,
                        "title": cand_title,
                        "artists": cand_artists,
                        "album": cand_album,
                        "duration_sec": cand_dur_sec,
                        "duration_formatted": cand_dur_str,
                        "source": "ytmusic_api",
                    })
            except Exception as e:
                logger.debug(f"ytmusicapi search error for '{query}': {e}")

        # 2. Fallback or augment with yt-dlp search if needed
        if not candidates:
            candidates = self._search_via_ytdlp(f"{query} audio", limit=5)

        if not candidates:
            return None

        # Score candidates
        scored_candidates: List[Tuple[float, Dict[str, Any]]] = []
        for cand in candidates:
            score = self._compute_match_score(
                target_title=title,
                target_artist=primary_artist,
                target_album=album,
                target_dur=target_duration,
                cand=cand,
                tolerance_seconds=tolerance_seconds,
            )
            scored_candidates.append((score, cand))

        # Sort by highest match score
        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        best_score, best_cand = scored_candidates[0]

        best_cand["match_score"] = round(best_score * 100, 1)
        best_cand["url"] = f"https://music.youtube.com/watch?v={best_cand['video_id']}"
        best_cand["watch_url"] = f"https://www.youtube.com/watch?v={best_cand['video_id']}"
        return best_cand

    def _compute_match_score(
        self,
        target_title: str,
        target_artist: str,
        target_album: str,
        target_dur: int,
        cand: Dict[str, Any],
        tolerance_seconds: int = 25,
    ) -> float:
        """Calculates a normalized score (0.0 to 1.0) for match quality."""
        # 1. Title Similarity (0.0 to 0.40)
        clean_target = clean_title_for_search(target_title)
        clean_cand = clean_title_for_search(cand["title"])
        sim = _string_similarity(clean_target, clean_cand)
        title_score = sim * 0.40

        # 2. Artist Similarity (0.0 to 0.30)
        cand_artists = cand.get("artists", "")
        if target_artist and cand_artists:
            art_sim = _string_similarity(target_artist, cand_artists)
            artist_score = art_sim * 0.30
        else:
            artist_score = 0.15

        # 3. Duration match (0.0 to 0.20)
        dur_score = 0.0
        if target_dur > 0 and cand.get("duration_sec", 0) > 0:
            diff = abs(target_dur - cand["duration_sec"])
            if diff <= 3:
                dur_score = 0.20
            elif diff <= 10:
                dur_score = 0.15
            elif diff <= tolerance_seconds:
                dur_score = 0.08
            else:
                dur_score = 0.0
        else:
            dur_score = 0.10

        # 4. Album match bonus (0.0 to 0.10)
        album_score = 0.0
        if target_album and cand.get("album"):
            if _string_similarity(target_album, cand["album"]) > 0.7:
                album_score = 0.10

        total = title_score + artist_score + dur_score + album_score
        return min(total, 1.0)

    def _search_via_ytdlp(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Fallback search using yt-dlp."""
        ydl_opts: Dict[str, Any] = {
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
        }
        if self.cookies_file:
            ydl_opts["cookiefile"] = self.cookies_file

        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                if not info or "entries" not in info:
                    return []
                for entry in info["entries"]:
                    if not entry or not entry.get("id"):
                        continue
                    dur = int(entry.get("duration") or 0)
                    mins = dur // 60
                    secs = dur % 60
                    results.append({
                        "video_id": entry["id"],
                        "title": entry.get("title", ""),
                        "artists": entry.get("uploader", "") or entry.get("channel", ""),
                        "album": "",
                        "duration_sec": dur,
                        "duration_formatted": f"{mins:02d}:{secs:02d}",
                        "source": "ytdlp_search",
                    })
        except Exception as e:
            logger.debug(f"yt-dlp fallback search failed: {e}")
        return results

    def download_audio(
        self,
        video_id: str,
        output_path_without_ext: str,
        bitrate_kbps: int = 320,
        progress_hook: Optional[Any] = None,
    ) -> bool:
        """
        Downloads YouTube Music audio stream using yt-dlp and transcodes to MP3.
        
        Args:
            video_id: YouTube video ID.
            output_path_without_ext: Destination path without .mp3 extension.
            bitrate_kbps: Audio bitrate (320, 160, 96).
            progress_hook: Optional yt-dlp progress callback.
            
        Returns:
            True if download succeeded, False otherwise.
        """
        ydl_opts: Dict[str, Any] = {
            "format": "bestaudio/best",
            "outtmpl": f"{output_path_without_ext}.%(ext)s",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": str(bitrate_kbps),
                }
            ],
            "quiet": True,
            "no_warnings": True,
        }

        if self.cookies_file:
            ydl_opts["cookiefile"] = self.cookies_file

        if progress_hook:
            ydl_opts["progress_hooks"] = [progress_hook]

        url = f"https://www.youtube.com/watch?v={video_id}"
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
            mp3_path = f"{output_path_without_ext}.mp3"
            return os.path.exists(mp3_path)
        except Exception as e:
            logger.error(f"Failed to download audio via yt-dlp for {video_id}: {e}")
            return False
