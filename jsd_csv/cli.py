"""
Command-Line Interface and Argument Parser for JSD-CSV.
Supports both non-interactive switch-based execution and a sleek interactive wizard.
"""

import argparse
import sys
from typing import List, Optional

from . import __app_name__, __description__, __version__
from .downloader import DownloaderEngine
from .ui import console, print_banner, prompt_interactive_options


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

  # Download entire album with custom filename template:
  jsd-csv -u "https://www.jiosaavn.com/album/.../..." -t "{track} - {title}" -o ./album

  # Only export CSV metadata (no audio downloaded):
  jsd-csv -u "https://www.jiosaavn.com/featured/.../..." -m csv -o ./csv_export

  # Download only audio files (no CSV) using YouTube Music fallback:
  jsd-csv -u "Kesariya Arijit Singh" -m songs -s auto --cookies ./cookies.txt

Supported Filename Identifiers:
  {title}         Song title
  {artist}        Primary artist name
  {artists}       All artists (comma-separated)
  {album}         Album name
  {year}          Release year
  {track}         Padded track number (01, 02...)
  {track_number}  Raw track number (1, 2...)
  {id}            JioSaavn song ID
  {duration}      Duration (e.g. 03-45)
  {language}      Song language
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

    parser = build_parser()
    args = parser.parse_args(argv)

    print_banner()

    # Determine whether to run interactive mode
    if args.interactive or not args.url:
        config = prompt_interactive_options()
        engine = DownloaderEngine(
            output_dir=config["output"],
            mode=config["mode"],
            quality=config["quality"],
            source=config["source"],
            template=config["template"],
            fetch_lyrics=config["lyrics"],
            embed_cover=config["cover"],
            cookies_file=config["cookies"],
        )
        total, success, csv_path = engine.run(config["url"], auto_confirm=False)
    else:
        engine = DownloaderEngine(
            output_dir=args.output,
            mode=args.mode,
            quality=args.quality,
            source=args.source,
            template=args.template,
            fetch_lyrics=args.lyrics,
            embed_cover=args.cover,
            cookies_file=args.cookies,
            csv_filename=args.csv_name,
        )
        total, success, csv_path = engine.run(args.url, auto_confirm=args.yes)

    return 0 if (total > 0 and success > 0) or (args.mode == "csv" and total > 0) else 1


if __name__ == "__main__":
    sys.exit(main())
