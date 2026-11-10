"""
MP3 ID3 Metadata Tagger.
Embeds comprehensive metadata including Title, Artists, Album, Year, Track Number,
Genre/Language, Record Label, Copyright, Lyrics, and high-resolution Album Art.
"""

import logging
import os
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
    TPE2,
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
        song_metadata: Song metadata dict (loaded on the fly or from CSV).
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

        # Track Artists (TPE1) - Deduplicated essential musical performers only (no actors/cast)
        raw_artists = (
            song_metadata.get("artists")
            or song_metadata.get("all_artists")
            or song_metadata.get("primary_artists")
            or song_metadata.get("artist")
            or ""
        )
        clean_artists_list = []
        seen_artists = set()
        for a in [x.strip() for x in raw_artists.split(",") if x.strip()]:
            if a.lower() not in seen_artists:
                seen_artists.add(a.lower())
                clean_artists_list.append(a)
        clean_artists = ", ".join(clean_artists_list)
        if clean_artists:
            tags.setall("TPE1", [TPE1(encoding=3, text=clean_artists)])

        # Album Artist (TPE2) - Separate dedicated tag for Album Artist / Music Composer
        album_artist = (
            song_metadata.get("album_artist")
            or song_metadata.get("music")
            or (clean_artists_list[0] if clean_artists_list else "")
        )
        if album_artist:
            tags.setall("TPE2", [TPE2(encoding=3, text=str(album_artist).strip())])

        # Album
        album = song_metadata.get("album", "")
        if album:
            tags.setall("TALB", [TALB(encoding=3, text=album)])

        # Year
        year = str(song_metadata.get("year", ""))
        if year:
            tags.setall("TDRC", [TDRC(encoding=3, text=year)])

        # Track Number
        track_num = song_metadata.get("track_number") or song_metadata.get("track")
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
            img_source = song_metadata.get("image", "") or song_metadata.get("album_art_url", "")
            if img_source:
                img_data = None
                mime_type = "image/jpeg"
                try:
                    # 1. Local image file
                    if os.path.exists(img_source) and os.path.isfile(img_source):
                        with open(img_source, "rb") as f:
                            img_data = f.read()
                        if img_source.lower().endswith(".png"):
                            mime_type = "image/png"
                    # 2. Remote image URL
                    elif img_source.startswith(("http://", "https://")):
                        s = session or requests.Session()
                        r = s.get(img_source, timeout=12)
                        if r.status_code == 200 and r.content:
                            img_data = r.content
                            if "png" in img_source.lower():
                                mime_type = "image/png"

                    if img_data:
                        tags.setall(
                            "APIC",
                            [
                                APIC(
                                    encoding=3,
                                    mime=mime_type,
                                    type=3,  # Front cover
                                    desc="Cover",
                                    data=img_data,
                                )
                            ],
                        )
                except Exception as e:
                    logger.debug(f"Failed to embed album cover from {img_source}: {e}")

        tags.save(mp3_file_path, v2_version=3)
        return True
    except Exception as e:
        logger.error(f"Failed to tag MP3 file '{mp3_file_path}': {e}")
        return False
