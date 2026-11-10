"""
Sleek, High-Color Rich Terminal User Interface for JSD-CSV.
Provides stylized gradient banners, colorful badge prompts, track overview tables,
and vivid completion summaries with clean ASCII styling and zero emojis.
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

from rich import box
from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

console = Console(legacy_windows=False)


def render_gradient_banner() -> Panel:
    """Builds a crisp, perfectly aligned two-tone gradient ASCII banner with badge highlights."""
    banner_lines = [
        r"    ██╗███████╗██████╗        ██████╗███████╗██╗   ██╗",
        r"    ██║██╔════╝██╔══██╗      ██╔════╝██╔════╝██║   ██║",
        r"    ██║███████╗██║  ██║█████╗██║     ███████╗██║   ██║",
        r"    ██║╚════██║██║  ██║╚════╝██║     ╚════██║╚██╗ ██╔╝",
        r"██████║███████║██████╔╝      ╚██████╗███████║ ╚████╔╝ ",
        r"╚═════╝╚══════╝╚═════╝        ╚═════╝╚══════╝  ╚═══╝  ",
    ]

    banner = Text()
    for line in banner_lines:
        banner.append(line[:23], style="bold #00f0ff")
        banner.append(line[23:30], style="bold bright_white")
        banner.append(line[30:], style="bold #d946ef")
        banner.append("\n")

    # Badges bar (no emojis)
    badges = Text()
    badges.append(" JioSaavn Downloader with CSV ", style="bold bright_white")
    badges.append(" | ", style="bold #facc15")
    badges.append("v1.0.0\n", style="bold bright_cyan")
    badges.append(" [320 KBPS] ", style="bold white on #0284c7")
    badges.append(" ", style="default")
    badges.append(" [YT MUSIC FALLBACK] ", style="bold white on #7c3aed")
    badges.append(" ", style="default")
    badges.append(" [CSV BATCH] ", style="bold white on #059669")
    badges.append(" ", style="default")
    badges.append(" [ID3 + ART] ", style="bold white on #d97706")
    badges.append(" ", style="default")
    badges.append(" [FULL LYRICS] ", style="bold white on #e11d48")

    content = Text()
    content.append_text(banner)
    content.append("\n")
    content.append_text(badges)

    return Panel(
        Align.center(content),
        box=box.ROUNDED,
        border_style="bright_cyan",
        padding=(0, 2),
    )


def print_banner() -> None:
    """Renders the sleek JSD-CSV banner in full color."""
    console.print(render_gradient_banner())
    console.print()


def prompt_interactive_options() -> Dict[str, Any]:
    """
    Runs the sleek interactive setup wizard with vibrant badge numbers and styled options.
    Returns a dictionary of parsed options.
    """
    console.print("[bold #38bdf8]=== [/][bold #a855f7]::[/] [bold bright_white]INTERACTIVE CONFIGURATION WIZARD[/] [bold #a855f7]::[/][bold #38bdf8] ===[/]")
    console.print("[dim]Configure your download parameters below or press Enter to accept defaults.[/dim]\n")

    # Step 1: Optional CSV
    console.print("[bold white on #7c3aed] 1 [/] [bold bright_white]Load tracks from an existing CSV file or online URL[/] [dim](optional)[/]")
    csv_input = Prompt.ask(
        "    [bold #38bdf8]?[/] [bold]CSV Path or Online URL [dim](press Enter to skip)[/dim][/bold]",
        default="",
    ).strip().strip("'\"")

    url_input = ""
    if not csv_input:
        # Step 2: JioSaavn Link or Query
        console.print("\n[bold white on #0284c7] 2 [/] [bold bright_white]Enter JioSaavn Link or Search Query[/]")
        while True:
            url_input = Prompt.ask(
                "    [bold #38bdf8]?[/] [bold]JioSaavn URL or Search Query[/bold]"
            )
            if url_input.strip():
                break
            console.print("    [red]Input cannot be empty. Please enter a valid link, query, or CSV path.[/red]")
            
        clean_url = url_input.strip().strip("'\"")
        if clean_url.lower().endswith(".csv") or ".csv?" in clean_url.lower() or (os.path.exists(clean_url) and os.path.isfile(clean_url)):
            csv_input = clean_url
            url_input = ""

    # Step 3: Output Directory
    console.print("\n[bold white on #059669] 3 [/] [bold bright_white]Target Output Directory[/]")
    out_dir = Prompt.ask(
        "    [bold #38bdf8]?[/] [bold]Destination Folder[/bold]",
        default="./downloads",
    )

    # Step 4: Mode Selection
    console.print("\n[bold white on #d97706] 4 [/] [bold bright_white]Select Operational Mode[/]")
    console.print("    [bold #38bdf8]1)[/] [bold bright_white]Both[/] [dim](Download MP3s + Export/Update CSV Metadata)[/] [bold white on #059669] RECOMMENDED [/]")
    console.print("    [bold #38bdf8]2)[/] [bold bright_white]Songs Only[/] [dim](Download MP3s without writing a CSV file)[/]")
    console.print("    [bold #38bdf8]3)[/] [bold bright_white]CSV Only[/] [dim](Fast metadata sync to CSV without downloading audio)[/]")
    mode_choice = Prompt.ask(
        "    [bold #38bdf8]?[/] [bold]Choose Mode[/bold]",
        choices=["1", "2", "3"],
        default="1",
    )
    mode_map = {"1": "all", "2": "songs", "3": "csv"}
    selected_mode = mode_map[mode_choice]

    # Step 5: Audio Quality (if downloading songs)
    selected_quality = "320"
    if selected_mode in ("all", "songs"):
        console.print("\n[bold white on #db2777] 5 [/] [bold bright_white]Select Target Audio Bitrate[/]")
        console.print("    [bold #38bdf8]1)[/] [bold #4ade80]320 kbps[/] [dim](Extreme Studio Fidelity)[/] [bold white on #16a34a] MAXIMUM [/]")
        console.print("    [bold #38bdf8]2)[/] [bold #38bdf8]160 kbps[/] [dim](Standard High Quality)[/]")
        console.print("    [bold #38bdf8]3)[/] [bold #fbbf24]96 kbps[/]  [dim](Fast / Bandwidth Saver)[/]")
        q_choice = Prompt.ask(
            "    [bold #38bdf8]?[/] [bold]Choose Bitrate[/bold]",
            choices=["1", "2", "3"],
            default="1",
        )
        q_map = {"1": "320", "2": "160", "3": "96"}
        selected_quality = q_map[q_choice]

    # Step 6: Audio Stream Source
    selected_source = "auto"
    if selected_mode in ("all", "songs"):
        console.print("\n[bold white on #4f46e5] 6 [/] [bold bright_white]Select Audio Stream Engine[/]")
        console.print("    [bold #38bdf8]1)[/] [bold #c084fc]Auto[/] [dim](JioSaavn CDN stream + YT Music fallback)[/] [bold white on #7e22ce] DUAL ENGINE [/]")
        console.print("    [bold #38bdf8]2)[/] [bold #38bdf8]JioSaavn Direct[/] [dim](Raw master audio stream directly from CDN)[/]")
        console.print("    [bold #38bdf8]3)[/] [bold #f87171]YouTube Music[/] [dim](Matched audio stream via YouTube Music)[/]")
        src_choice = Prompt.ask(
            "    [bold #38bdf8]?[/] [bold]Choose Engine[/bold]",
            choices=["1", "2", "3"],
            default="1",
        )
        src_map = {"1": "auto", "2": "saavn", "3": "ytmusic"}
        selected_source = src_map[src_choice]

    # Step 7: Filename Template
    console.print("\n[bold white on #0d9488] 7 [/] [bold bright_white]Custom Filename Pattern[/]")
    console.print("    [dim]Supported tags: {artist}, {title}, {album}, {year}, {track}, {id}, {duration}, {language}[/dim]")
    template = Prompt.ask(
        "    [bold #38bdf8]?[/] [bold]Filename Pattern[/bold]",
        default="{artist} - {title}",
    )

    # Step 8: Lyrics
    console.print("\n[bold white on #ea580c] 8 [/] [bold bright_white]ID3 Tagging & Lyrics Embedding[/]")
    fetch_lyrics = Confirm.ask(
        "    [bold #38bdf8]?[/] [bold]Fetch and embed full lyrics into MP3 tags?[/bold]",
        default=True,
    )

    # Step 9: Cookies file
    console.print("\n[bold white on #dc2626] 9 [/] [bold bright_white]YouTube Music Authentication / Cookies[/] [dim](optional)[/]")
    cookies_input = Prompt.ask(
        "    [bold #38bdf8]?[/] [bold]Path to cookies.txt [dim](press Enter to skip)[/dim][/bold]",
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
    """Displays collection header details before track listing with rich badges (no emojis)."""
    raw_type = meta.get("type", "Collection").lower()
    title = meta.get("title", "Unknown")
    artist = meta.get("artist", "")
    count = meta.get("count", 0)
    source = meta.get("source", "")

    header_text = Text()

    # Badges for types
    type_badge_map = {
        "csv": (" [CSV BATCH] ", "bold white on #059669"),
        "album": (" [ALBUM] ", "bold white on #2563eb"),
        "playlist": (" [PLAYLIST] ", "bold white on #7c3aed"),
        "artist": (" [ARTIST TOP] ", "bold white on #d97706"),
        "song": (" [SINGLE] ", "bold white on #db2777"),
        "search": (" [SEARCH RESULTS] ", "bold white on #0891b2"),
    }
    badge_label, badge_style = type_badge_map.get(raw_type, (" [COLLECTION] ", "bold white on #4b5563"))
    header_text.append(badge_label, style=badge_style)
    header_text.append(" ")
    header_text.append(title, style="bold bright_white")

    if artist and raw_type != "csv":
        header_text.append("   |  ", style="dim yellow")
        header_text.append("Artist: ", style="bold cyan")
        header_text.append(artist, style="bright_white")

    if source and raw_type == "csv":
        header_text.append("   |  ", style="dim yellow")
        header_text.append("Source: ", style="bold cyan")
        short_src = source if len(source) <= 50 else source[:47] + "..."
        header_text.append(short_src, style="dim white")

    header_text.append("   |  ", style="dim yellow")
    header_text.append(f" {count} TRACKS ", style="bold black on #4ade80")

    console.print(Panel(header_text, box=box.ROUNDED, border_style="bright_blue", padding=(0, 1)))


def display_tracks_table(songs: List[Dict[str, Any]], max_rows: int = 25) -> None:
    """Displays a neat, colorful table of tracks about to be processed (no emojis)."""
    table = Table(
        title="[bold #38bdf8]=== Found Tracks Preview ===[/bold #38bdf8]",
        title_justify="left",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold #c084fc",
        show_lines=False,
    )
    table.add_column("#", style="dim cyan", width=4, justify="right")
    table.add_column("Title", style="bold bright_white", min_width=25, no_wrap=True)
    table.add_column("Artist(s)", style="bold #38bdf8", min_width=20, no_wrap=True)
    table.add_column("Album", style="bold #facc15", min_width=18, no_wrap=True)
    table.add_column("Duration", style="bold #4ade80", width=10, justify="center")
    table.add_column("Lyrics", style="bold #f472b6", width=10, justify="center")

    display_list = songs[:max_rows]
    for idx, s in enumerate(display_list):
        lyrics_icon = "[bold #22c55e][LYRICS][/]" if s.get("has_lyrics") or s.get("lyrics") else "[dim]--[/]"
        dur_fmt = s.get("duration_formatted", "00:00")
        table.add_row(
            f"{s.get('track_number') or idx + 1:02d}",
            s.get("title", "Unknown")[:35],
            (s.get("primary_artists") or s.get("artist") or "Unknown")[:28],
            s.get("album", "Unknown")[:25],
            dur_fmt,
            lyrics_icon,
        )

    console.print(table)
    if len(songs) > max_rows:
        console.print(f"  [dim cyan]... and {len(songs) - max_rows} more tracks[/dim cyan]\n")
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
    """Renders a sleek, colorful dashboard summary card upon completion (no emojis)."""
    summary_table = Table.grid(padding=(0, 2))
    summary_table.add_column(style="bold cyan", justify="right")
    summary_table.add_column(style="bright_white")

    summary_table.add_row(
        "[bold white on #16a34a] COMPLETED [/]",
        f"[bold bright_green]{success_count}[/] / [bold bright_white]{total}[/] tracks successfully processed",
    )
    if failed_count > 0:
        summary_table.add_row(
            "[bold white on #dc2626] FAILED [/]",
            f"[bold red]{failed_count}[/] tracks encountered errors or skipped",
        )
    summary_table.add_row(
        "[bold white on #0284c7] OUTPUT [/]",
        f"[bold bright_cyan]{os.path.abspath(output_dir)}[/bold bright_cyan]",
    )
    if csv_path and os.path.exists(csv_path):
        summary_table.add_row(
            "[bold white on #7c3aed] CSV RECORD [/]",
            f"[bold bright_magenta]{os.path.abspath(csv_path)}[/bold bright_magenta]",
        )
    mins, secs = divmod(int(elapsed_seconds), 60)
    summary_table.add_row(
        "[bold white on #d97706] TIME [/]",
        f"[bold #facc15]{mins}m {secs:02d}s[/bold #facc15]",
    )

    panel = Panel(
        summary_table,
        title="[bold bright_white]JSD-CSV Pipeline Complete[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_green",
        padding=(1, 2),
    )
    console.print(panel)
