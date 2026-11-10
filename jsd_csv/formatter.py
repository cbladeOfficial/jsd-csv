"""
Filename formatting and cross-platform filesystem sanitization.
Supports customizable naming patterns like '{artist} - {title}', '{album}/{track} - {title}', etc.
"""

import os
import re
from typing import Any, Dict

# Windows reserved names that cannot be used as filenames or directories
WINDOWS_RESERVED = {
    "CON", "PRN", "AUX", "NUL",
    "COM1", "COM2", "COM3", "COM4", "COM5", "COM6", "COM7", "COM8", "COM9",
    "LPT1", "LPT2", "LPT3", "LPT4", "LPT5", "LPT6", "LPT7", "LPT8", "LPT9",
}


def sanitize_filename_component(name: str, max_length: int = 120) -> str:
    """
    Sanitizes a single filename component (basename or directory name).
    Removes invalid characters and handles Windows reserved device names.
    """
    if not name:
        return "Unknown"

    # Replace characters that are illegal on Windows / POSIX: < > : " / \ | ? *
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", str(name))
    
    # Strip ASCII control characters (0x00 to 0x1f)
    sanitized = re.sub(r"[\x00-\x1f\x7f]", "", sanitized)

    # Collapse repeated whitespace or underscores
    sanitized = re.sub(r"\s+", " ", sanitized)
    sanitized = re.sub(r"_+", "_", sanitized)

    # Remove leading and trailing spaces and dots (problematic on Windows)
    sanitized = sanitized.strip(" .")

    if not sanitized:
        sanitized = "Unknown"

    # Check for Windows reserved names
    base_upper = sanitized.split(".")[0].upper()
    if base_upper in WINDOWS_RESERVED:
        sanitized = f"_{sanitized}"

    # Truncate length if needed
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length].rstrip(" ._")

    return sanitized


def sanitize_path(path_str: str) -> str:
    r"""
    Sanitizes an entire relative path composed of directory names and a filename.
    Separators (/ or \) are respected as directory dividers.
    """
    normalized = path_str.replace("\\", "/")
    parts = normalized.split("/")
    sanitized_parts = [
        sanitize_filename_component(part)
        for part in parts
        if part.strip() and part != "."
    ]
    return os.path.join(*sanitized_parts) if sanitized_parts else "output"


def format_filename(template: str, metadata: Dict[str, Any]) -> str:
    """
    Formats a filename using template placeholders and song metadata.
    Supports spotDL-style and JSD-CSV placeholders (case-insensitive, with hyphens or underscores).
    
    Supported placeholders:
      {title}, {song}, {name}                - Track title
      {artist}, {primary_artist}             - Primary lead artist
      {artists}, {all_artists}               - All track artists (comma-separated)
      {album_artist}, {albumartist}          - Album artist / primary music composer
      {album}, {album_name}                  - Album name
      {year}, {release_year}                 - Release year
      {date}, {release_date}, {original_date}- Full release date
      {track}, {track_number}, {tracknumber} - Zero-padded track number (e.g. 01, 02)
      {raw_track}, {track_raw}               - Unpadded track number (e.g. 1, 2)
      {tracks_count}, {total_tracks}         - Total tracks count in album/playlist
      {disc}, {disc_number}                  - Disc number (e.g. 01)
      {disc_count}, {total_discs}            - Total discs count (e.g. 1)
      {duration}                             - Formatted duration (e.g. 04-28)
      {duration_seconds}, {duration_sec}     - Duration in seconds (e.g. 268)
      {language}, {genre}                    - Track language / genre
      {publisher}, {label}, {record_label}   - Publisher / Record label
      {copyright}                            - Copyright text
      {id}, {track_id}, {song_id}            - JioSaavn song ID
      {isrc}                                 - ISRC identifier
      {bitrate}, {quality}                   - Bitrate quality (e.g. 320 kbps)
      {list_name}, {playlist}                - Collection or playlist title
      {list_position}, {playlist_index}      - Position in playlist (padded 01, 02)
      {list_length}, {list_count}            - Total items in playlist
      {output_ext}, {ext}                    - Audio extension (mp3)
    
    Args:
        template: Custom naming string like '{artists} - {title}' or '{album}/{track} - {title}'
        metadata: Dictionary containing track information.
        
    Returns:
        A sanitized, formatted filename (without extension).
    """
    if not template or not template.strip():
        template = "{artist} - {title}"

    # Compute track numbers
    raw_track = metadata.get("track_number") or metadata.get("track") or metadata.get("list_position") or 1
    try:
        track_int = int(raw_track)
        padded_track = f"{track_int:02d}"
    except (ValueError, TypeError):
        padded_track = str(raw_track)
        track_int = 1

    # Total tracks count
    total_tracks_val = metadata.get("total_tracks") or metadata.get("tracks_count") or metadata.get("list_length") or ""
    try:
        total_int = int(total_tracks_val)
        padded_total = f"{total_int:02d}"
    except (ValueError, TypeError):
        padded_total = str(total_tracks_val)

    # Disc number
    raw_disc = metadata.get("disc_number") or metadata.get("disc") or 1
    try:
        disc_int = int(raw_disc)
        padded_disc = f"{disc_int:02d}"
    except (ValueError, TypeError):
        padded_disc = str(raw_disc)

    # Duration
    duration_str = str(metadata.get("duration_formatted", "")).replace(":", "-")
    duration_sec = str(metadata.get("duration", "") or 0)

    # Primary and All Artists
    primary_artist = str(
        metadata.get("primary_artists")
        or metadata.get("primary_artist")
        or metadata.get("artist")
        or "Unknown Artist"
    )
    all_artists = str(
        metadata.get("artists")
        or metadata.get("all_artists")
        or primary_artist
    )
    album_artist = str(
        metadata.get("album_artist")
        or metadata.get("music")
        or primary_artist
    )

    lookup: Dict[str, str] = {
        # Titles
        "title": str(metadata.get("title") or "Unknown Title"),
        "song": str(metadata.get("title") or "Unknown Title"),
        "name": str(metadata.get("title") or "Unknown Title"),
        "track_title": str(metadata.get("title") or "Unknown Title"),

        # Artists
        "artist": primary_artist,
        "primary_artist": primary_artist,
        "primaryartist": primary_artist,
        "artists": all_artists,
        "all_artists": all_artists,
        "allartists": all_artists,
        "album_artist": album_artist,
        "albumartist": album_artist,
        "composer": album_artist,

        # Album
        "album": str(metadata.get("album") or "Unknown Album"),
        "album_name": str(metadata.get("album") or "Unknown Album"),

        # Year & Dates
        "year": str(metadata.get("year") or ""),
        "release_year": str(metadata.get("year") or ""),
        "date": str(metadata.get("release_date") or metadata.get("year") or ""),
        "release_date": str(metadata.get("release_date") or metadata.get("year") or ""),
        "original_date": str(metadata.get("release_date") or metadata.get("year") or ""),

        # Track & Disc Numbers
        "track": padded_track,
        "track_number": padded_track,
        "tracknumber": padded_track,
        "raw_track": str(raw_track),
        "track_raw": str(raw_track),
        "tracks_count": padded_total or str(total_tracks_val),
        "track_count": padded_total or str(total_tracks_val),
        "total_tracks": str(total_tracks_val),
        "disc": padded_disc,
        "disc_number": padded_disc,
        "discnumber": padded_disc,
        "disc_count": str(metadata.get("disc_count") or "1"),
        "total_discs": str(metadata.get("disc_count") or "1"),

        # Duration
        "duration": duration_str,
        "duration_formatted": duration_str,
        "duration_seconds": duration_sec,
        "duration_sec": duration_sec,

        # Genre & Language
        "language": str(metadata.get("language") or ""),
        "genre": str(metadata.get("language") or ""),

        # Publisher / Label
        "publisher": str(metadata.get("label") or ""),
        "label": str(metadata.get("label") or ""),
        "record_label": str(metadata.get("label") or ""),
        "copyright": str(metadata.get("copyright") or ""),

        # Identifiers
        "id": str(metadata.get("id") or ""),
        "track_id": str(metadata.get("id") or ""),
        "song_id": str(metadata.get("id") or ""),
        "isrc": str(metadata.get("isrc") or ""),

        # Quality / Bitrate
        "bitrate": str(metadata.get("bitrate") or "320 kbps"),
        "quality": str(metadata.get("bitrate") or "320 kbps"),

        # Playlist / Collection List Context
        "list_name": str(metadata.get("list_name") or metadata.get("playlist_title") or ""),
        "playlist": str(metadata.get("list_name") or metadata.get("playlist_title") or ""),
        "playlist_name": str(metadata.get("list_name") or metadata.get("playlist_title") or ""),
        "list_position": padded_track,
        "playlist_index": padded_track,
        "list_length": str(total_tracks_val),
        "list_count": str(total_tracks_val),

        # Output extension (spotdl compatibility)
        "output_ext": "mp3",
        "ext": "mp3",
    }

    def replace_token(match: re.Match) -> str:
        raw_token = match.group(1).lower()
        norm_token = raw_token.replace("-", "_")
        no_us_token = norm_token.replace("_", "")
        if norm_token in lookup:
            val = lookup[norm_token]
            return sanitize_filename_component(val)
        elif no_us_token in lookup:
            val = lookup[no_us_token]
            return sanitize_filename_component(val)
        return match.group(0)

    # Replace {placeholder} patterns (supporting letters, digits, underscores, and hyphens)
    result = re.sub(r"\{([a-zA-Z0-9_\-]+)\}", replace_token, template)

    # Sanitize the full path structure
    return sanitize_path(result)
