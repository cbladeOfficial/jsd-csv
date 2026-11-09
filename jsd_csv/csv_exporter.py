"""
CSV Metadata Exporter.
Exports rich song and collection metadata into a standardized CSV file in the output directory.
Uses UTF-8 with BOM (utf-8-sig) for native compatibility with Microsoft Excel and Google Sheets.
"""

import csv
import logging
import os
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

CSV_HEADERS = [
    "Track Number",
    "Title",
    "Artists",
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
    "Full Lyrics",
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
    # Ensure lyrics do not break CSV rendering by normalizing newlines
    full_lyrics = item.get("lyrics", "") or ""
    
    return [
        item.get("track_number", ""),
        item.get("title", ""),
        item.get("all_artists", ""),
        item.get("primary_artists", ""),
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
        full_lyrics,
        item.get("yt_title", ""),
        item.get("yt_video_id", ""),
        item.get("yt_url", ""),
        item.get("yt_match_score", ""),
        item.get("audio_source", ""),
        item.get("filename", ""),
        item.get("file_path", ""),
        item.get("download_status", "Pending"),
    ]


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
