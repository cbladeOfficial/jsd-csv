"""
CSV Metadata Exporter and Importer.
Exports rich song metadata into a standardized CSV file (utf-8-sig)
and imports previously exported CSV files (local paths or online URLs)
to resume, batch, or re-download songs later.
"""

import csv
import io
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

import requests

logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "Track Number",
    "Title",
    "Artists",
    "Album Artist",
    "Primary Artist",
    "Album",
    "Year",
    "Release Date",
    "Duration (Formatted)",
    "Duration (Seconds)",
    "Bitrate",
    "Language",
    "Record Label",
    "Copyright",
    "JioSaavn ID",
    "JioSaavn URL",
    "Album Art URL",
    "Has Lyrics",
    "Lyrics Snippet",
    "YT Music Title",
    "YT Music Video ID",
    "YT Music URL",
    "YT Match Score (%)",
    "Audio Source",
    "Filename",
    "File Path",
    "Download Status",
]


def format_row(item: Dict[str, Any]) -> List[Any]:
    """Flattens a song record dictionary into a CSV row."""
    artists = item.get("artists") or item.get("all_artists") or item.get("artist") or ""
    album_artist = item.get("album_artist") or item.get("music") or ""
    primary_artist = item.get("primary_artists") or (artists.split(",")[0].strip() if artists else "")
    if not album_artist:
        album_artist = primary_artist

    return [
        item.get("track_number", ""),
        item.get("title", ""),
        artists,
        album_artist,
        primary_artist,
        item.get("album", ""),
        item.get("year", ""),
        item.get("release_date", ""),
        item.get("duration_formatted", ""),
        item.get("duration", 0),
        item.get("bitrate", "320 kbps"),
        item.get("language", ""),
        item.get("label", ""),
        item.get("copyright", ""),
        item.get("id", ""),
        item.get("perma_url", ""),
        item.get("image", ""),
        "Yes" if item.get("has_lyrics") else "No",
        item.get("lyrics_snippet", ""),
        item.get("yt_title", ""),
        item.get("yt_video_id", ""),
        item.get("yt_url", ""),
        item.get("yt_match_score", ""),
        item.get("audio_source", ""),
        item.get("filename", ""),
        item.get("file_path", ""),
        item.get("download_status", "Pending"),
    ]


def _normalize_key(header: str) -> str:
    """Normalizes column names for fuzzy header matching."""
    return re.sub(r"[^a-z0-9]", "", str(header).lower())


def load_csv(source: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """
    Loads song metadata records from a local CSV file or online HTTP/HTTPS URL.
    
    Args:
        source: Local file path (e.g. './downloads/songs.csv') or remote URL (e.g. 'https://.../songs.csv').
        
    Returns:
        Tuple of (collection_metadata, list_of_song_records).
    """
    source_clean = source.strip().strip("'\"")
    is_remote = source_clean.startswith(("http://", "https://"))

    raw_text: str = ""
    title: str = "Imported CSV"

    if is_remote:
        logger.info(f"Downloading CSV from online URL: {source_clean}")
        resp = requests.get(source_clean, timeout=20)
        resp.raise_for_status()
        raw_text = resp.text
        url_part = source_clean.split("?")[0].rstrip("/").split("/")[-1]
        title = os.path.splitext(url_part)[0] or "Online CSV"
    else:
        abs_path = os.path.abspath(source_clean)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"CSV file not found: {abs_path}")
        title = os.path.splitext(os.path.basename(abs_path))[0]
        # Read with utf-8-sig first, fallback to utf-8 / latin-1
        try:
            with open(abs_path, "r", encoding="utf-8-sig") as f:
                raw_text = f.read()
        except UnicodeDecodeError:
            with open(abs_path, "r", encoding="latin-1") as f:
                raw_text = f.read()

    reader = csv.reader(io.StringIO(raw_text))
    rows = list(reader)
    if not rows:
        return {"type": "csv", "title": title, "count": 0, "source": source_clean}, []

    raw_headers = rows[0]
    col_map: Dict[str, int] = {_normalize_key(h): idx for idx, h in enumerate(raw_headers)}

    def get_val(row: List[str], *aliases: str, default: Any = "") -> Any:
        for alias in aliases:
            norm = _normalize_key(alias)
            if norm in col_map and col_map[norm] < len(row):
                val = row[col_map[norm]].strip()
                if val:
                    return val
        return default

    songs: List[Dict[str, Any]] = []
    for idx, r in enumerate(rows[1:], 1):
        if not any(cell.strip() for cell in r):
            continue

        raw_title = get_val(r, "Title", "Song", "Track Name", default=f"Track {idx}")
        raw_artists = get_val(r, "Artists", "All Artists", default="")
        raw_album_artist = get_val(r, "Album Artist", default="")
        raw_primary = get_val(r, "Primary Artist", "Artist", default="")
        if not raw_primary and raw_artists:
            raw_primary = raw_artists.split(",")[0].strip()
        if not raw_artists and raw_primary:
            raw_artists = raw_primary
        if not raw_album_artist:
            raw_album_artist = raw_primary

        raw_album = get_val(r, "Album", default="")
        raw_year = get_val(r, "Year", default="")
        raw_release = get_val(r, "Release Date", default="")

        # Duration
        raw_dur_sec = get_val(r, "Duration (Seconds)", "Duration (Sec)", "Duration", default="0")
        try:
            dur_sec = int(float(raw_dur_sec))
        except (ValueError, TypeError):
            dur_sec = 0

        raw_dur_fmt = get_val(r, "Duration (Formatted)", default="")
        if not raw_dur_fmt and dur_sec > 0:
            raw_dur_fmt = f"{dur_sec // 60:02d}:{dur_sec % 60:02d}"

        # Track number
        raw_track_no = get_val(r, "Track Number", "Track #", "Track", default=str(idx))
        try:
            track_num = int(raw_track_no)
        except (ValueError, TypeError):
            track_num = idx

        has_lyrics_val = str(get_val(r, "Has Lyrics", default="false")).lower() in ("yes", "true", "1")

        song_dict = {
            "track_number": track_num,
            "title": raw_title,
            "artists": raw_artists,
            "all_artists": raw_artists,
            "album_artist": raw_album_artist,
            "primary_artists": raw_primary,
            "artist": raw_primary,
            "album": raw_album,
            "year": raw_year,
            "release_date": raw_release,
            "duration": dur_sec,
            "duration_formatted": raw_dur_fmt or "00:00",
            "bitrate": get_val(r, "Bitrate", default="320 kbps"),
            "language": get_val(r, "Language", default=""),
            "label": get_val(r, "Record Label", "Label", default=""),
            "copyright": get_val(r, "Copyright", default=""),
            "id": get_val(r, "JioSaavn ID", "Song ID", "ID", default=""),
            "perma_url": get_val(r, "JioSaavn URL", "URL", "Link", default=""),
            "image": get_val(r, "Album Art URL", "Image", "Cover", default=""),
            "has_lyrics": has_lyrics_val,
            "lyrics_snippet": get_val(r, "Lyrics Snippet", default=""),
            "lyrics": get_val(r, "Full Lyrics", "Lyrics", default=""),
            "yt_title": get_val(r, "YT Music Title", default=""),
            "yt_video_id": get_val(r, "YT Music Video ID", "Video ID", default=""),
            "yt_url": get_val(r, "YT Music URL", default=""),
            "yt_match_score": get_val(r, "YT Match Score (%)", default=""),
            "audio_source": get_val(r, "Audio Source", default=""),
            "filename": get_val(r, "Filename", default=""),
            "file_path": get_val(r, "File Path", default=""),
            "download_status": get_val(r, "Download Status", default="Pending"),
            "from_csv": True,
        }
        songs.append(song_dict)

    collection_meta = {
        "type": "csv",
        "title": title,
        "artist": songs[0]["primary_artists"] if songs else "",
        "image": songs[0]["image"] if songs else "",
        "count": len(songs),
        "source": source_clean,
    }
    return collection_meta, songs


class CSVExporter:
    """Manages exporting and appending metadata records to a CSV file."""

    def __init__(self, output_dir: str, csv_filename: Optional[str] = None):
        self.output_dir = os.path.abspath(output_dir)
        os.makedirs(self.output_dir, exist_ok=True)
        self.csv_filename = csv_filename or "metadata.csv"
        if not self.csv_filename.lower().endswith(".csv"):
            self.csv_filename += ".csv"
        self.csv_path = os.path.join(self.output_dir, self.csv_filename)

    def write_all(self, records: List[Dict[str, Any]]) -> str:
        """Writes all records to the CSV file, overwriting or creating anew."""
        try:
            with open(self.csv_path, mode="w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerow(CSV_HEADERS)
                for item in records:
                    writer.writerow(format_row(item))
            logger.info(f"Saved CSV metadata with {len(records)} tracks to: {self.csv_path}")
            return self.csv_path
        except Exception as e:
            logger.error(f"Failed to write CSV file '{self.csv_path}': {e}")
            raise

    def append_record(self, item: Dict[str, Any]) -> str:
        """Appends a single record to the CSV file, writing headers if newly created."""
        file_exists = os.path.exists(self.csv_path) and os.path.getsize(self.csv_path) > 0
        try:
            with open(self.csv_path, mode="a", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                if not file_exists:
                    writer.writerow(CSV_HEADERS)
                writer.writerow(format_row(item))
            return self.csv_path
        except Exception as e:
            logger.error(f"Failed to append to CSV file '{self.csv_path}': {e}")
            raise
