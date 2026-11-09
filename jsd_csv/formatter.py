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
    
    Supported placeholders (case-insensitive):
      {title}         - Song title
      {artist}        - Primary artist name
      {artists}       - All artists (comma-separated)
      {album}         - Album name
      {year}          - Release year
      {track}         - Track number padded (e.g. 01, 02)
      {track_number}  - Raw track number (1, 2, ...)
      {id}            - JioSaavn song ID
      {duration}      - Formatted duration (e.g. 03-45)
      {language}      - Song language (e.g. Hindi)
    
    Args:
        template: Custom naming string like '{artist} - {title}' or '{album}/{track} - {title}'
        metadata: Dictionary containing track information.
        
    Returns:
        A sanitized, formatted filename (without extension).
    """
    if not template or not template.strip():
        template = "{artist} - {title}"

    # Build lowercased lookup map for case-insensitive matching
    raw_track = metadata.get("track_number") or metadata.get("track") or 1
    try:
        track_int = int(raw_track)
        padded_track = f"{track_int:02d}"
    except (ValueError, TypeError):
        padded_track = str(raw_track)

    duration_str = str(metadata.get("duration_formatted", "")).replace(":", "-")

    lookup: Dict[str, str] = {
        "title": str(metadata.get("title") or "Unknown Title"),
        "artist": str(metadata.get("primary_artists") or metadata.get("primary_artist") or metadata.get("artist") or "Unknown Artist"),
        "artists": str(metadata.get("all_artists") or metadata.get("artists") or "Unknown Artists"),
        "album": str(metadata.get("album") or "Unknown Album"),
        "year": str(metadata.get("year") or ""),
        "track": padded_track,
        "track_number": str(raw_track),
        "id": str(metadata.get("id") or ""),
        "duration": duration_str,
        "language": str(metadata.get("language") or ""),
    }

    def replace_token(match: re.Match) -> str:
        token = match.group(1).lower()
        if token in lookup:
            val = lookup[token]
            return sanitize_filename_component(val)
        return match.group(0)

    # Replace {placeholder} patterns
    result = re.sub(r"\{([a-zA-Z0-9_]+)\}", replace_token, template)

    # Sanitize the full path structure
    return sanitize_path(result)
