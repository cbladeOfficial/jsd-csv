"""
Command-Line Interface and Argument Parser for JSD-CSV.
Supports both non-interactive switch-based execution and a sleek interactive wizard.
"""

import argparse
import sys
from typing import List, Optional

from . import __app_name__, __description__, __version__
from .config import find_default_config, load_config, save_config
from .downloader import DownloaderEngine
from .ui import console, print_banner, print_interrupt_message, prompt_interactive_options


def build_parser() -> argparse.ArgumentParser:
    """Builds the CLI argument parser with all flags and help descriptions."""
    parser = argparse.ArgumentParser(
        prog="jsd-csv",
        description=f"{__app_name__}: {__description__}",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Launch sleek interactive mode:
  jsd-csv

  # Download single song with CSV at 320 kbps:
  jsd-csv -u "https://www.jiosaavn.com/song/.../..." -o ./my_songs

  # Download songs from a local CSV file:
  jsd-csv -f ./my_songs/metadata.csv -o ./downloaded_music

  # Download songs from an online CSV URL:
  jsd-csv -f "https://example.com/playlist.csv" -o ./downloaded_music

  # Download entire album with custom filename template:
  jsd-csv -u "https://www.jiosaavn.com/album/.../..." -t "{track} - {title}" -o ./album

  # Only export CSV metadata (no audio downloaded):
  jsd-csv -u "https://www.jiosaavn.com/featured/.../..." -m csv -o ./csv_export

  # Download only audio files (no CSV) using YouTube Music fallback:
  jsd-csv -u "Kesariya Arijit Singh" -m songs -s auto --cookies ./cookies.txt

Supported Filename Identifiers (supports {tag} or {tag-name}):
  {title}           Song title ({song}, {name})
  {artist}          Primary lead artist
  {artists}         All track artists comma-separated ({all-artists})
  {album_artist}    Album artist / music composer ({albumartist}, {album-artist})
  {album}           Album name ({album-name})
  {year}            Release year ({release-year})
  {date}            Full release date ({release-date}, {original-date})
  {track}           Padded track number e.g. 01, 02 ({track-number}, {tracknumber})
  {raw_track}       Raw unpadded track number e.g. 1, 2
  {tracks_count}    Total tracks in collection ({total-tracks})
  {disc}            Disc number ({disc-number})
  {duration}        Formatted duration e.g. 04-28
  {duration_sec}    Duration in seconds e.g. 268 ({duration-seconds})
  {language}        Song language ({genre})
  {publisher}       Record label / publisher ({label})
  {id}              JioSaavn song ID ({track-id})
  {list_name}       Collection or playlist title ({playlist})
  {list_position}   Position in playlist/collection ({playlist-index})
  {output_ext}      Audio file extension e.g. mp3
        """,
    )

    parser.add_argument(
        "-u", "--url",
        dest="url",
        type=str,
        default=None,
        help="JioSaavn URL (song, album, playlist, artist) or search query.",
    )

    parser.add_argument(
        "-f", "--from-csv", "--csv-input",
        dest="from_csv",
        type=str,
        default=None,
        help="Path or URL to an existing CSV file to load and download tracks from (optional).",
    )

    parser.add_argument(
        "-o", "--output",
        dest="output",
        type=str,
        default="./downloads",
        help="Output directory where audio files and CSV are saved (default: ./downloads).",
    )

    parser.add_argument(
        "-m", "--mode",
        dest="mode",
        type=str,
        choices=["all", "songs", "csv"],
        default="all",
        help="Download mode: 'all' (songs + CSV), 'songs' (only songs), 'csv' (only CSV). Default: all.",
    )

    parser.add_argument(
        "-t", "--template",
        dest="template",
        type=str,
        default="{artist} - {title}",
        help="Custom filename template, e.g. '{artist} - {title}' or '{album}/{track} - {title}'.",
    )

    parser.add_argument(
        "--artists-separator", "--artist-separator",
        dest="artists_separator",
        type=str,
        default=", ",
        help="Separator string used between multiple artists in {artists} filename tag: ', ', '/', ' & ', ' | ' (default: ', ').",
    )

    parser.add_argument(
        "-q", "--quality",
        dest="quality",
        type=str,
        choices=["320", "160", "96"],
        default="320",
        help="Target audio bitrate quality in kbps (320, 160, 96). Default: 320.",
    )

    parser.add_argument(
        "-s", "--source",
        dest="source",
        type=str,
        choices=["auto", "saavn", "ytmusic"],
        default="auto",
        help="Audio source: 'auto' (Saavn CDN with YT Music fallback), 'saavn' (direct only), 'ytmusic' (YT Music only).",
    )

    parser.add_argument(
        "-c", "--cookies",
        dest="cookies",
        type=str,
        default=None,
        help="Path to cookies.txt file for YouTube Music authentication / bot bypass.",
    )

    parser.add_argument(
        "--lyrics",
        dest="lyrics",
        action="store_true",
        default=True,
        help="Fetch and embed full song lyrics if available (default: enabled).",
    )
    parser.add_argument(
        "--no-lyrics",
        dest="lyrics",
        action="store_false",
        help="Do not fetch full song lyrics.",
    )

    parser.add_argument(
        "--cover",
        dest="cover",
        action="store_true",
        default=True,
        help="Download and embed high-resolution album cover into MP3 (default: enabled).",
    )
    parser.add_argument(
        "--no-cover",
        dest="cover",
        action="store_false",
        help="Do not embed album cover.",
    )

    parser.add_argument(
        "--csv-name",
        dest="csv_name",
        type=str,
        default=None,
        help="Custom name for the metadata CSV file (default: derived from collection title).",
    )

    parser.add_argument(
        "-C", "--config",
        dest="config_file",
        type=str,
        default=None,
        help="Path to a JSON configuration file to load download settings from.",
    )

    parser.add_argument(
        "--save-config",
        dest="save_config_file",
        type=str,
        nargs="?",
        const="config.json",
        default=None,
        help="Save current parameters to a JSON configuration file (default: config.json).",
    )

    parser.add_argument(
        "--id3-version",
        dest="id3_version",
        type=int,
        choices=[3, 4],
        default=4,
        help="ID3v2 tag version to write: 4 (default, native multi-artist null separation) or 3 (legacy slash separation).",
    )

    parser.add_argument(
        "-y", "--yes",
        dest="yes",
        action="store_true",
        default=False,
        help="Automatically confirm and proceed with download without prompting.",
    )

    parser.add_argument(
        "-i", "--interactive",
        dest="interactive",
        action="store_true",
        default=False,
        help="Force launch interactive configuration wizard.",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{__app_name__} v{__version__}",
        help="Show program version and exit.",
    )

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entrypoint for JSD-CSV CLI."""
    if argv is None:
        argv = sys.argv[1:]

    try:
        parser = build_parser()
        args = parser.parse_args(argv)

        print_banner()

        # 1. Resolve configuration profile
        cfg_file = args.config_file
        loaded_cfg = None
        if cfg_file:
            try:
                loaded_cfg = load_config(cfg_file)
                console.print(f"  [bold green]Loaded configuration from:[/] [bold cyan]{cfg_file}[/bold cyan]\n")
            except Exception as e:
                console.print(f"[bold red]Error loading config file '{cfg_file}':[/bold red] {e}")
                return 1
        elif not args.url and not args.from_csv and not args.interactive:
            # Check if default config exists in current directory
            default_cfg = find_default_config()
            if default_cfg:
                try:
                    loaded_cfg = load_config(default_cfg)
                    cfg_file = default_cfg
                except Exception:
                    loaded_cfg = None

        # Merge configuration if present
        effective_url = args.url
        effective_csv = args.from_csv
        effective_output = args.output
        effective_mode = args.mode
        effective_quality = args.quality
        effective_source = args.source
        effective_template = args.template
        effective_artists_separator = args.artists_separator
        effective_lyrics = args.lyrics
        effective_cover = args.cover
        effective_cookies = args.cookies
        effective_id3_version = args.id3_version

        if loaded_cfg:
            if not effective_url and loaded_cfg.get("url"):
                effective_url = loaded_cfg.get("url")
            if not effective_csv and loaded_cfg.get("csv"):
                effective_csv = loaded_cfg.get("csv")
            if not any(a in argv for a in ("-o", "--output")) and loaded_cfg.get("output"):
                effective_output = loaded_cfg.get("output")
            if not any(a in argv for a in ("-m", "--mode")) and loaded_cfg.get("mode"):
                effective_mode = loaded_cfg.get("mode")
            if not any(a in argv for a in ("-q", "--quality")) and loaded_cfg.get("quality"):
                effective_quality = str(loaded_cfg.get("quality"))
            if not any(a in argv for a in ("-s", "--source")) and loaded_cfg.get("source"):
                effective_source = loaded_cfg.get("source")
            if not any(a in argv for a in ("-t", "--template")) and loaded_cfg.get("template"):
                effective_template = loaded_cfg.get("template")
            if not any(a.startswith(("--artists-separator", "--artist-separator")) for a in argv) and "artists_separator" in loaded_cfg:
                effective_artists_separator = str(loaded_cfg["artists_separator"])
            if not any(a in argv for a in ("--lyrics", "--no-lyrics")) and "lyrics" in loaded_cfg:
                effective_lyrics = bool(loaded_cfg.get("lyrics"))
            if not any(a in argv for a in ("--cover", "--no-cover")) and "cover" in loaded_cfg:
                effective_cover = bool(loaded_cfg.get("cover"))
            if not any(a in argv for a in ("-c", "--cookies")) and loaded_cfg.get("cookies"):
                effective_cookies = loaded_cfg.get("cookies")
            if not any(a in argv for a in ("--id3-version",)) and loaded_cfg.get("id3_version"):
                effective_id3_version = int(loaded_cfg.get("id3_version"))

        # Determine whether to run interactive mode
        is_interactive = args.interactive or (not effective_url and not effective_csv)

        if is_interactive:
            config = prompt_interactive_options(existing_config=loaded_cfg, config_filename=cfg_file)
            # Handle save-config if requested via CLI flag
            if args.save_config_file:
                save_config(config, args.save_config_file)
                console.print(f"  [bold green]Settings saved to:[/] [bold cyan]{args.save_config_file}[/bold cyan]\n")

            engine = DownloaderEngine(
                output_dir=config["output"],
                mode=config["mode"],
                quality=config["quality"],
                source=config["source"],
                template=config["template"],
                artists_separator=config.get("artists_separator", effective_artists_separator),
                fetch_lyrics=config["lyrics"],
                embed_cover=config["cover"],
                cookies_file=config["cookies"],
                id3_version=config.get("id3_version", effective_id3_version),
            )
            total, success, csv_path = engine.run(
                input_target=config.get("url"),
                csv_source=config.get("csv"),
                auto_confirm=False,
            )
        else:
            # Save config if flag passed
            if args.save_config_file:
                saved_dict = {
                    "url": effective_url,
                    "csv": effective_csv,
                    "output": effective_output,
                    "mode": effective_mode,
                    "quality": effective_quality,
                    "source": effective_source,
                    "template": effective_template,
                    "artists_separator": effective_artists_separator,
                    "lyrics": effective_lyrics,
                    "cover": effective_cover,
                    "cookies": effective_cookies,
                    "id3_version": effective_id3_version,
                }
                save_config(saved_dict, args.save_config_file)
                console.print(f"  [bold green]Settings saved to:[/] [bold cyan]{args.save_config_file}[/bold cyan]\n")

            engine = DownloaderEngine(
                output_dir=effective_output,
                mode=effective_mode,
                quality=effective_quality,
                source=effective_source,
                template=effective_template,
                artists_separator=effective_artists_separator,
                fetch_lyrics=effective_lyrics,
                embed_cover=effective_cover,
                cookies_file=effective_cookies,
                csv_filename=args.csv_name,
                id3_version=effective_id3_version,
            )
            total, success, csv_path = engine.run(
                input_target=effective_url,
                csv_source=effective_csv,
                auto_confirm=args.yes,
            )

        if getattr(engine, "interrupted", False):
            return 130

        return 0 if (total > 0 and success > 0) or (effective_mode == "csv" and total > 0) else 1

    except KeyboardInterrupt:
        print_interrupt_message()
        return 130


if __name__ == "__main__":
    sys.exit(main())
