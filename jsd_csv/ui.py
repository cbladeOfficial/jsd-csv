"""
Sleek Rich-based Terminal User Interface for JSD-CSV.
Provides stylized banners, interactive prompts, track overview tables,
and download completion summaries.
"""

import os
import sys
from typing import Any, Dict, List, Optional, Tuple

# Reconfigure stdout/stderr for cross-platform UTF-8 support
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

console = Console(legacy_windows=False)

BANNER_ART = r"""
     ██╗███████╗██████╗         ██████╗███████╗██╗   ██╗
     ██║██╔════╝██╔══██╗       ██╔════╝██╔════╝██║   ██║
     ██║███████╗██║  ██║ █████╗██║     ███████╗██║   ██║
██   ██║╚════██║██║  ██║ ╚════╝██║     ╚════██║╚██╗ ██╔╝
╚█████╔╝███████║██████╔╝       ╚██████╗███████║ ╚████╔╝ 
 ╚════╝ ╚══════╝╚═════╝         ╚═════╝╚══════╝  ╚═══╝  
"""


def print_banner() -> None:
    """Renders the sleek JSD-CSV banner in cyan and violet."""
    title_text = Text(BANNER_ART, style="bold cyan")
    subtitle = Text("Jio Saavn Downloader - (with) CSV  |  v1.0.0", style="bold magenta")
    banner_panel = Panel(
        Align.center(title_text + "\n" + subtitle),
        border_style="bright_blue",
        padding=(0, 2),
    )
    console.print(banner_panel)
    console.print()


def prompt_interactive_options() -> Dict[str, Any]:
    """
    Runs the sleek interactive setup wizard when no CLI switches are passed.
    Returns a dictionary of parsed options.
    """
    console.print("[bold yellow]❯ Interactive Configuration Wizard[/bold yellow]")
    console.print("[dim]Enter the details below or press Enter to accept the defaults.[/dim]\n")

    # 1. CSV Path or URL (optional)
    console.print("[dim]You can paste a path or URL to an existing CSV file to download songs from,")
    console.print("or leave it blank to enter a JioSaavn link/query instead.[/dim]")
    csv_input = Prompt.ask(
        "[bold bright_green]?[/bold bright_green] [bold]CSV Path or Online URL (optional, press Enter to skip)[/bold]",
        default="",
    ).strip().strip("'\"")

    url_input = ""
    if not csv_input:
        while True:
            url_input = Prompt.ask("[bold bright_green]?[/bold bright_green] [bold]Enter JioSaavn Link or Search Query[/bold]")
            if url_input.strip():
                break
            console.print("[red]Input cannot be empty. Please enter a valid link, query, or CSV path.[/red]")
        # Check if the user entered a CSV into the link prompt
        clean_url = url_input.strip().strip("'\"")
        if clean_url.lower().endswith(".csv") or ".csv?" in clean_url.lower() or (os.path.exists(clean_url) and os.path.isfile(clean_url)):
            csv_input = clean_url
            url_input = ""

    # 2. Output Directory
    out_dir = Prompt.ask(
        "[bold bright_green]?[/bold bright_green] [bold]Output Directory[/bold]",
        default="./downloads",
    )

    # 3. Mode Selection
    console.print("\n[bold]Select Operation Mode:[/bold]")
    console.print("  [cyan]1[/cyan]) [bold]Both[/bold] (Download MP3s + Export/Update CSV Metadata) [green][Recommended][/green]")
    console.print("  [cyan]2[/cyan]) [bold]Songs Only[/bold] (Download MP3s without updating CSV)")
    console.print("  [cyan]3[/cyan]) [bold]CSV Only[/bold] (Export/Sync CSV Metadata without downloading audio)")
    mode_choice = Prompt.ask(
        "[bold bright_green]?[/bold bright_green] [bold]Mode[/bold]",
        choices=["1", "2", "3"],
        default="1",
    )
    mode_map = {"1": "all", "2": "songs", "3": "csv"}
    selected_mode = mode_map[mode_choice]

    # 4. Audio Quality (only if songs are to be downloaded)
    selected_quality = "320"
    if selected_mode in ("all", "songs"):
        console.print("\n[bold]Select Target Audio Bitrate:[/bold]")
        console.print("  [cyan]1[/cyan]) [bold]320 kbps[/bold] (Extreme High Definition) [green][Recommended][/green]")
        console.print("  [cyan]2[/cyan]) [bold]160 kbps[/bold] (Standard Quality)")
        console.print("  [cyan]3[/cyan]) [bold]96 kbps[/bold]  (Compressed / Fast)")
        q_choice = Prompt.ask(
            "[bold bright_green]?[/bold bright_green] [bold]Quality[/bold]",
            choices=["1", "2", "3"],
            default="1",
        )
        q_map = {"1": "320", "2": "160", "3": "96"}
        selected_quality = q_map[q_choice]

    # 5. Audio Source preference
    selected_source = "auto"
    if selected_mode in ("all", "songs"):
        console.print("\n[bold]Select Audio Stream Source:[/bold]")
        console.print("  [cyan]1[/cyan]) [bold]Auto[/bold] (JioSaavn CDN direct stream, fallback to YouTube Music) [green][Recommended][/green]")
        console.print("  [cyan]2[/cyan]) [bold]JioSaavn Direct Only[/bold] (Get raw files directly from JioSaavn)")
        console.print("  [cyan]3[/cyan]) [bold]YouTube Music Only[/bold] (Download matched exact audio from YT Music)")
        src_choice = Prompt.ask(
            "[bold bright_green]?[/bold bright_green] [bold]Audio Source[/bold]",
            choices=["1", "2", "3"],
            default="1",
        )
        src_map = {"1": "auto", "2": "saavn", "3": "ytmusic"}
        selected_source = src_map[src_choice]

    # 6. Filename Template
    template = Prompt.ask(
        "\n[bold bright_green]?[/bold bright_green] [bold]Filename Template[/bold] [dim](e.g. '{artist} - {title}' or '{album}/{track} - {title}')[/dim]",
        default="{artist} - {title}",
    )

    # 7. Lyrics
    fetch_lyrics = Confirm.ask(
        "[bold bright_green]?[/bold bright_green] [bold]Fetch and embed full lyrics if available?[/bold]",
        default=True,
    )

    # 8. Cookies file
    cookies_input = Prompt.ask(
        "[bold bright_green]?[/bold bright_green] [bold]Path to cookies.txt for YouTube Music (optional, press Enter to skip)[/bold]",
        default="",
    )
    cookies_path = cookies_input.strip() if cookies_input.strip() and os.path.exists(cookies_input.strip()) else None

    console.print()
    return {
        "url": url_input.strip(),
        "csv": csv_input.strip(),
        "output": out_dir.strip(),
        "mode": selected_mode,
        "quality": selected_quality,
        "source": selected_source,
        "template": template.strip(),
        "lyrics": fetch_lyrics,
        "cookies": cookies_path,
        "cover": True,
    }


def display_collection_header(meta: Dict[str, Any]) -> None:
    """Displays collection header details before track listing."""
    raw_type = meta.get("type", "Collection")
    title = meta.get("title", "Unknown")
    artist = meta.get("artist", "")
    count = meta.get("count", 0)
    source = meta.get("source", "")

    header_text = Text()
    if raw_type.lower() == "csv":
        header_text.append("CSV Batch: ", style="bold bright_blue")
        header_text.append(title, style="bold bright_white")
        if source:
            header_text.append("  •  Source: ", style="bold cyan")
            header_text.append(source[:55] + ("..." if len(source) > 55 else ""), style="bright_white")
    else:
        header_text.append(f"{raw_type.capitalize()}: ", style="bold bright_blue")
        header_text.append(title, style="bold bright_white")
        if artist:
            header_text.append("  •  Artist: ", style="bold cyan")
            header_text.append(artist, style="bright_white")
            
    header_text.append("  •  Total Tracks: ", style="bold green")
    header_text.append(str(count), style="bold yellow")

    console.print(Panel(header_text, border_style="bright_blue"))


def display_tracks_table(songs: List[Dict[str, Any]], max_rows: int = 25) -> None:
    """Displays a neat table of tracks about to be processed."""
    table = Table(
        title="[bold cyan]Found Tracks[/bold cyan]",
        title_justify="left",
        border_style="dim",
        header_style="bold magenta",
        show_lines=False,
    )
    table.add_column("#", style="dim", width=4, justify="right")
    table.add_column("Title", style="bold white", min_width=25, no_wrap=True)
    table.add_column("Artist(s)", style="cyan", min_width=20, no_wrap=True)
    table.add_column("Album", style="yellow", min_width=18, no_wrap=True)
    table.add_column("Duration", style="green", width=10, justify="center")
    table.add_column("Lyrics", style="bright_blue", width=8, justify="center")

    display_list = songs[:max_rows]
    for idx, s in enumerate(display_list):
        lyrics_icon = "[green]✓[/green]" if s.get("has_lyrics") or s.get("lyrics") else "[dim]—[/dim]"
        table.add_row(
            str(s.get("track_number") or idx + 1),
            s.get("title", "Unknown")[:35],
            (s.get("primary_artists") or s.get("artist") or "Unknown")[:28],
            s.get("album", "Unknown")[:25],
            s.get("duration_formatted", "00:00"),
            lyrics_icon,
        )

    console.print(table)
    if len(songs) > max_rows:
        console.print(f"[dim]... and {len(songs) - max_rows} more tracks[/dim]\n")
    else:
        console.print()


def display_summary_report(
    total: int,
    success_count: int,
    failed_count: int,
    csv_path: Optional[str],
    output_dir: str,
    elapsed_seconds: float,
) -> None:
    """Renders a sleek completion panel with processing statistics."""
    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column(style="bold cyan", justify="right")
    summary_table.add_column(style="bright_white")

    summary_table.add_row("Total Processed:", f"{total} tracks")
    summary_table.add_row("Successfully Downloaded:", f"[bold green]{success_count}[/bold green]")
    if failed_count > 0:
        summary_table.add_row("Failed / Skipped:", f"[bold red]{failed_count}[/bold red]")
    summary_table.add_row("Output Directory:", os.path.abspath(output_dir))
    if csv_path and os.path.exists(csv_path):
        summary_table.add_row("CSV Metadata File:", f"[bold green]{os.path.abspath(csv_path)}[/bold green]")
    mins, secs = divmod(int(elapsed_seconds), 60)
    summary_table.add_row("Elapsed Time:", f"{mins}m {secs}s")

    panel = Panel(
        summary_table,
        title="[bold green]✓ Download & Processing Complete[/bold green]",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)
