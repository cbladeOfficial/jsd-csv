"""
Core Download and Processing Engine for JSD-CSV.
Orchestrates metadata fetching, JioSaavn CDN streaming, FFmpeg transcoding,
YouTube Music fallback matching, MP3 ID3 tagging, and CSV exporting/importing.
"""

import logging
import os
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import requests
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeRemainingColumn,
)

from .api import JioSaavnAPI
from .csv_exporter import CSVExporter, load_csv
from .formatter import format_filename
from .tagger import embed_metadata
from .ui import (
    console,
    display_collection_header,
    display_summary_report,
    display_tracks_table,
)
from .ytmusic import YTMusicMatcher

logger = logging.getLogger(__name__)


def get_ffmpeg_path() -> Optional[str]:
    """Resolves FFmpeg path from system PATH, executable folder, or PyInstaller bundle."""
    # 1. Check system PATH
    found = shutil.which("ffmpeg")
    if found:
        return found

    binary_name = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"

    # 2. Check PyInstaller _MEIPASS bundle
    if hasattr(sys, "_MEIPASS"):
        bundle_path = os.path.join(sys._MEIPASS, binary_name)
        if os.path.exists(bundle_path):
            return bundle_path

    # 3. Check directory of running executable or script
    exe_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__))
    exe_ffmpeg = os.path.join(exe_dir, binary_name)
    if os.path.exists(exe_ffmpeg):
        return exe_ffmpeg

    # 4. Check current working directory
    cwd_ffmpeg = os.path.join(os.getcwd(), binary_name)
    if os.path.exists(cwd_ffmpeg):
        return cwd_ffmpeg

    return None


def check_ffmpeg() -> bool:
    """Checks if FFmpeg executable is accessible."""
    return get_ffmpeg_path() is not None


class DownloaderEngine:
    """Orchestrates track downloading, transcoding, tagging, and CSV generation/importing."""

    def __init__(
        self,
        output_dir: str = "./downloads",
        mode: str = "all",  # 'all' (songs+csv), 'songs', 'csv'
        quality: str = "320",  # '320', '160', '96'
        source: str = "auto",  # 'auto', 'saavn', 'ytmusic'
        template: str = "{artist} - {title}",
        fetch_lyrics: bool = True,
        embed_cover: bool = True,
        cookies_file: Optional[str] = None,
        csv_filename: Optional[str] = None,
    ):
        self.output_dir = os.path.abspath(output_dir)
        self.mode = mode.lower()
        self.quality = quality
        self.source = source.lower()
        self.template = template
        self.fetch_lyrics = fetch_lyrics
        self.embed_cover = embed_cover
        self.cookies_file = cookies_file
        self.csv_filename = csv_filename

        os.makedirs(self.output_dir, exist_ok=True)

        self.api = JioSaavnAPI()
        self.yt_matcher = YTMusicMatcher(cookies_file=self.cookies_file, ffmpeg_path=get_ffmpeg_path())
        self.session = requests.Session()

    def run(
        self,
        input_target: Optional[str] = None,
        csv_source: Optional[str] = None,
        auto_confirm: bool = False,
    ) -> Tuple[int, int, Optional[str]]:
        """
        Executes the main pipeline.
        
        Args:
            input_target: JioSaavn URL, search query, or CSV path.
            csv_source: Optional path or URL to an existing CSV file.
            auto_confirm: If True, skips interactive confirmation prompt.
            
        Returns:
            Tuple of (total_processed, successful_downloads, csv_file_path).
        """
        start_time = time.time()

        if self.mode in ("all", "songs") and not check_ffmpeg():
            console.print(
                "[bold red]Error: FFmpeg is not installed or not found in system PATH.[/bold red]\n"
                "[yellow]FFmpeg is required to transcode audio streams into high-quality MP3 format.[/yellow]\n"
                "[dim]Please install FFmpeg or place ffmpeg.exe next to jsd-csv.exe and try again.[/dim]"
            )
            return 0, 0, None

        # Determine if loading from CSV
        active_csv_source = None
        if csv_source and str(csv_source).strip():
            active_csv_source = str(csv_source).strip()
        elif input_target:
            clean_tgt = str(input_target).strip().strip("'\"")
            if clean_tgt.lower().endswith(".csv") or ".csv?" in clean_tgt.lower() or (os.path.exists(clean_tgt) and os.path.isfile(clean_tgt)):
                active_csv_source = clean_tgt

        coll_meta: Dict[str, Any] = {}
        songs: List[Dict[str, Any]] = []

        if active_csv_source:
            with console.status(f"[bold cyan]Loading tracks from CSV: {active_csv_source}...[/bold cyan]", spinner="dots"):
                try:
                    coll_meta, songs = load_csv(active_csv_source)
                except Exception as e:
                    console.print(f"[bold red]Failed to load CSV file:[/bold red] {e}")
                    return 0, 0, None
        else:
            if not input_target or not str(input_target).strip():
                console.print("[bold red]Error: No URL, search query, or CSV input provided.[/bold red]")
                return 0, 0, None

            with console.status("[bold cyan]Fetching metadata from JioSaavn...[/bold cyan]", spinner="dots"):
                try:
                    coll_meta, songs = self.api.resolve_and_fetch(input_target)
                except Exception as e:
                    console.print(f"[bold red]Failed to fetch from JioSaavn:[/bold red] {e}")
                    return 0, 0, None

        if not songs:
            console.print("[bold red]No songs found to process.[/bold red]")
            return 0, 0, None

        # Display collection details and tracklist
        display_collection_header(coll_meta)
        display_tracks_table(songs)

        if not auto_confirm:
            from rich.prompt import Confirm
            action_desc = {
                "all": "download all audio tracks and update the CSV metadata",
                "songs": "download all audio tracks",
                "csv": "export the CSV metadata",
            }.get(self.mode, "proceed")
            if not Confirm.ask(f"[bold]Do you want to {action_desc}?[/bold]", default=True):
                console.print("[yellow]Operation cancelled by user.[/yellow]")
                return 0, 0, None

        # Prepare CSV filename
        if not self.csv_filename:
            safe_title = coll_meta.get("title", "metadata").strip().replace(" ", "_")
            safe_title = "".join(c for c in safe_title if c.isalnum() or c in ("_", "-"))
            self.csv_filename = f"{safe_title}_metadata.csv"

        csv_exporter = CSVExporter(self.output_dir, self.csv_filename) if self.mode in ("all", "csv") else None

        total_tracks = len(songs)
        success_count = 0
        failed_count = 0
        processed_records: List[Dict[str, Any]] = []

        # Rich Progress Bar setup with vivid color styling
        with Progress(
            SpinnerColumn(spinner_name="dots12", style="bold #d946ef"),
            TextColumn("[bold bright_white]{task.description}[/bold bright_white]"),
            BarColumn(complete_style="bold #c084fc", finished_style="bold #4ade80", pulse_style="bold #38bdf8"),
            TaskProgressColumn(text_format="[bold #facc15]{task.percentage:>3.0f}%[/bold #facc15]"),
            MofNCompleteColumn(),
            TimeRemainingColumn(compact=True),
            console=console,
        ) as progress:
            main_task = progress.add_task("[bold #38bdf8]▶ Processing tracks...[/bold #38bdf8]", total=total_tracks)

            for idx, song in enumerate(songs):
                track_title = song.get("title", "Unknown")
                track_num = idx + 1
                progress.update(main_task, description=f"[bold #38bdf8]▶ [{track_num}/{total_tracks}][/bold #38bdf8] [bold bright_white]{track_title[:32]}[/bold bright_white]")

                # If loaded from CSV, resolve any missing JioSaavn streams or details
                if song.get("from_csv"):
                    self._enrich_song_from_csv(song)

                # Fetch lyrics if enabled and needed
                if self.fetch_lyrics and not song.get("lyrics"):
                    if song.get("has_lyrics") or song.get("lyrics_id"):
                        lyrics_id = song.get("lyrics_id") or song.get("id")
                        if lyrics_id:
                            song["lyrics"] = self.api.get_lyrics(lyrics_id)

                # Search exact match on YouTube Music if not already recorded
                if not song.get("yt_video_id"):
                    try:
                        yt_match = self.yt_matcher.search_exact_match(song)
                        if yt_match:
                            song["yt_title"] = yt_match.get("title", "")
                            song["yt_video_id"] = yt_match.get("video_id", "")
                            song["yt_url"] = yt_match.get("url", "")
                            song["yt_match_score"] = yt_match.get("match_score", 0.0)
                    except Exception as e:
                        logger.debug(f"YT Music match failed for {track_title}: {e}")

                # Audio download handling
                song["bitrate"] = f"{self.quality} kbps"
                if self.mode == "csv":
                    song["download_status"] = "CSV Only"
                    success_count += 1
                else:
                    # Download audio & embed metadata tags + cover
                    ok = self._download_and_tag_track(song)
                    if ok:
                        song["download_status"] = "Downloaded"
                        success_count += 1
                    else:
                        song["download_status"] = "Failed"
                        failed_count += 1

                processed_records.append(song)
                progress.advance(main_task)

        # Write or update CSV file
        csv_path = None
        if csv_exporter:
            try:
                csv_path = csv_exporter.write_all(processed_records)
            except Exception as e:
                console.print(f"[bold red]Failed to write CSV file:[/bold red] {e}")

        # Summary report
        elapsed = time.time() - start_time
        display_summary_report(
            total=total_tracks,
            success_count=success_count,
            failed_count=failed_count,
            csv_path=csv_path,
            output_dir=self.output_dir,
            elapsed_seconds=elapsed,
        )

        return total_tracks, success_count, csv_path

    def _enrich_song_from_csv(self, song: Dict[str, Any]) -> None:
        """Enriches a song loaded from CSV with stream URLs and album art if missing."""
        if song.get("media_urls"):
            return

        # 1. Lookup by JioSaavn ID
        song_id = song.get("id")
        if song_id:
            try:
                res = self.api._call({"__call": "song.getDetails", "pids": song_id})
                api_songs = res.get("songs", [])
                if api_songs:
                    formatted = self.api.format_song_item(api_songs[0], song.get("track_number", 1))
                    if formatted.get("media_urls"):
                        song["media_urls"] = formatted["media_urls"]
                        song["decrypted_media_url"] = formatted["decrypted_media_url"]
                    if not song.get("image") and formatted.get("image"):
                        song["image"] = formatted["image"]
                    if not song.get("lyrics") and formatted.get("lyrics"):
                        song["lyrics"] = formatted["lyrics"]
                    return
            except Exception as e:
                logger.debug(f"Failed to lookup song by ID {song_id}: {e}")

        # 2. Lookup by JioSaavn URL
        perma_url = song.get("perma_url")
        if perma_url and ("jiosaavn.com" in perma_url or "saa.vn" in perma_url):
            try:
                _, api_songs = self.api.resolve_and_fetch(perma_url)
                if api_songs:
                    formatted = api_songs[0]
                    if formatted.get("media_urls"):
                        song["media_urls"] = formatted["media_urls"]
                        song["decrypted_media_url"] = formatted["decrypted_media_url"]
                    if not song.get("image") and formatted.get("image"):
                        song["image"] = formatted["image"]
                    return
            except Exception as e:
                logger.debug(f"Failed to lookup song by URL {perma_url}: {e}")

    def _download_and_tag_track(self, song: Dict[str, Any]) -> bool:
        """Downloads audio via JioSaavn direct or YT Music fallback, transcodes to MP3, and embeds tags."""
        rel_filename = format_filename(self.template, song)
        dest_mp3 = os.path.join(self.output_dir, f"{rel_filename}.mp3")
        os.makedirs(os.path.dirname(dest_mp3), exist_ok=True)

        song["filename"] = f"{os.path.basename(rel_filename)}.mp3"
        song["file_path"] = os.path.abspath(dest_mp3)

        # Skip download if already exists and non-empty
        if os.path.exists(dest_mp3) and os.path.getsize(dest_mp3) > 1024:
            song["audio_source"] = "Existing File"
            # Ensure tags and cover are up to date
            embed_metadata(
                mp3_file_path=dest_mp3,
                song_metadata=song,
                lyrics=song.get("lyrics"),
                embed_cover=self.embed_cover,
                session=self.session,
            )
            return True

        downloaded_source = None

        # Strategy 1: Attempt direct download from JioSaavn CDN
        if self.source in ("auto", "saavn"):
            direct_ok = self._try_saavn_direct_download(song, dest_mp3)
            if direct_ok:
                downloaded_source = "JioSaavn CDN"

        # Strategy 2: Fallback to YouTube Music
        if not downloaded_source and self.source in ("auto", "ytmusic"):
            yt_id = song.get("yt_video_id")
            if not yt_id:
                yt_match = self.yt_matcher.search_exact_match(song)
                if yt_match:
                    yt_id = yt_match.get("video_id")
                    song["yt_video_id"] = yt_id
                    song["yt_url"] = yt_match.get("url")
                    song["yt_title"] = yt_match.get("title")
            if yt_id:
                yt_ok = self._try_ytmusic_download(yt_id, dest_mp3)
                if yt_ok:
                    downloaded_source = "YouTube Music"

        if not downloaded_source or not os.path.exists(dest_mp3):
            return False

        song["audio_source"] = downloaded_source

        # Embed complete ID3 metadata, lyrics, and album cover
        embed_metadata(
            mp3_file_path=dest_mp3,
            song_metadata=song,
            lyrics=song.get("lyrics"),
            embed_cover=self.embed_cover,
            session=self.session,
        )

        return True

    def _try_saavn_direct_download(self, song: Dict[str, Any], dest_mp3: str) -> bool:
        """Downloads direct audio stream from JioSaavn CDN and converts to MP3."""
        media_urls = song.get("media_urls", {})
        if not media_urls:
            return False

        bitrate_order = [self.quality] + [q for q in ["320", "160", "96"] if q != self.quality]

        cdn_url = None
        for b in bitrate_order:
            cand = media_urls.get(b)
            if cand:
                try:
                    head = self.session.head(cand, timeout=5)
                    if head.status_code == 200:
                        cdn_url = cand
                        break
                except Exception:
                    pass

        if not cdn_url:
            cdn_url = song.get("decrypted_media_url")

        if not cdn_url:
            return False

        temp_dir = tempfile.gettempdir()
        temp_in = os.path.join(temp_dir, f"jsd_temp_{song.get('id', 'temp')}.mp4")

        try:
            with self.session.get(cdn_url, stream=True, timeout=25) as r:
                r.raise_for_status()
                with open(temp_in, "wb") as f:
                    for chunk in r.iter_content(chunk_size=65536):
                        if chunk:
                            f.write(chunk)

            if not os.path.exists(temp_in) or os.path.getsize(temp_in) < 1000:
                return False

            ffmpeg_bin = get_ffmpeg_path() or "ffmpeg"
            cmd = [
                ffmpeg_bin,
                "-y",
                "-i", temp_in,
                "-vn",
                "-c:a", "libmp3lame",
                "-b:a", f"{self.quality}k",
                dest_mp3,
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            return res.returncode == 0 and os.path.exists(dest_mp3) and os.path.getsize(dest_mp3) > 1000

        except Exception as e:
            logger.debug(f"Direct Saavn download failed for {song.get('title')}: {e}")
            return False
        finally:
            if os.path.exists(temp_in):
                try:
                    os.remove(temp_in)
                except Exception:
                    pass

    def _try_ytmusic_download(self, video_id: str, dest_mp3: str) -> bool:
        """Downloads audio track via YouTube Music using yt-dlp."""
        temp_base = os.path.splitext(dest_mp3)[0] + "_yttmp"
        try:
            bitrate_int = int(self.quality) if self.quality.isdigit() else 320
            ok = self.yt_matcher.download_audio(
                video_id=video_id,
                output_path_without_ext=temp_base,
                bitrate_kbps=bitrate_int,
            )
            created_mp3 = f"{temp_base}.mp3"
            if ok and os.path.exists(created_mp3):
                shutil.move(created_mp3, dest_mp3)
                return True
            return False
        except Exception as e:
            logger.debug(f"YouTube download failed for {video_id}: {e}")
            return False
        finally:
            for extra in [f"{temp_base}.mp3", f"{temp_base}.webm", f"{temp_base}.m4a"]:
                if os.path.exists(extra):
                    try:
                        os.remove(extra)
                    except Exception:
                        pass
