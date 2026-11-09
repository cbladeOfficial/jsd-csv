"""
MP3 ID3 Metadata Tagger.
Embeds comprehensive metadata including Title, Artists, Album, Year, Track Number,
Genre/Language, Record Label, Copyright, Lyrics, and high-resolution Album Art.
"""

import logging
from typing import Any, Dict, Optional

import requests
from mutagen.id3 import (
    APIC,
    COMM,
    ID3,
    ID3NoHeaderError,
    TALB,
    TCON,
    TCOP,
    TDRC,
    TIT2,
    TPE1,
    TPUB,
    TRCK,
    USLT,
)

logger = logging.getLogger(__name__)


def embed_metadata(
    mp3_file_path: str,
    song_metadata: Dict[str, Any],
    lyrics: Optional[str] = None,
    embed_cover: bool = True,
    session: Optional[requests.Session] = None,
) -> bool:
    """
    Embeds complete ID3v2 tags and cover art into an MP3 file.
    
    Args:
        mp3_file_path: Path to the .mp3 file.
        song_metadata: Song metadata dict.
        lyrics: Clean full plaintext lyrics (optional).
        embed_cover: Whether to download and embed the high-res cover image.
        session: Requests session for downloading artwork.
        
    Returns:
        True if tagged successfully, False otherwise.
    """
    try:
        try:
            tags = ID3(mp3_file_path)
        except ID3NoHeaderError:
            tags = ID3()

        # Title
        title = song_metadata.get("title", "")
        if title:
            tags.setall("TIT2", [TIT2(encoding=3, text=title)])

        # Artists
        artists = song_metadata.get("all_artists") or song_metadata.get("primary_artists") or ""
        if artists:
            tags.setall("TPE1", [TPE1(encoding=3, text=artists)])

        # Album
        album = song_metadata.get("album", "")
        if album:
            tags.setall("TALB", [TALB(encoding=3, text=album)])

        # Year
        year = str(song_metadata.get("year", ""))
        if year:
            tags.setall("TDRC", [TDRC(encoding=3, text=year)])

        # Track Number
        track_num = song_metadata.get("track_number")
        if track_num:
            tags.setall("TRCK", [TRCK(encoding=3, text=str(track_num))])

        # Language / Genre
        lang = song_metadata.get("language", "")
        if lang:
            tags.setall("TCON", [TCON(encoding=3, text=lang)])

        # Publisher / Record Label
        label = song_metadata.get("label", "")
        if label:
            tags.setall("TPUB", [TPUB(encoding=3, text=label)])

        # Copyright
        copyright_txt = song_metadata.get("copyright", "")
        if copyright_txt:
            tags.setall("TCOP", [TCOP(encoding=3, text=copyright_txt)])

        # Comment
        tags.setall("COMM", [COMM(encoding=3, lang="eng", desc="", text="Archived with JSD-CSV")])

        # Lyrics (USLT frame)
        lyrics_text = lyrics or song_metadata.get("lyrics", "") or song_metadata.get("lyrics_snippet", "")
        if lyrics_text and lyrics_text.strip():
            tags.setall(
                "USLT",
                [USLT(encoding=3, lang="eng", desc="", text=lyrics_text.strip())],
            )

        # Album Art (APIC frame)
        if embed_cover:
            img_url = song_metadata.get("image", "")
            if img_url:
                try:
                    s = session or requests.Session()
                    r = s.get(img_url, timeout=12)
                    if r.status_code == 200 and r.content:
                        mime_type = "image/jpeg"
                        if "png" in img_url.lower():
                            mime_type = "image/png"
                        tags.setall(
                            "APIC",
                            [
                                APIC(
                                    encoding=3,
                                    mime=mime_type,
                                    type=3,  # Front cover
                                    desc="Cover",
                                    data=r.content,
                                )
                            ],
                        )
                except Exception as e:
                    logger.debug(f"Failed to download/embed album cover from {img_url}: {e}")

        tags.save(mp3_file_path, v2_version=3)
        return True
    except Exception as e:
        logger.error(f"Failed to tag MP3 file '{mp3_file_path}': {e}")
        return False
