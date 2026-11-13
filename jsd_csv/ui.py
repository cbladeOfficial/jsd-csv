"""
Sleek, High-Color Rich Terminal User Interface for JSD-CSV.
Provides stylized gradient banners, solid box badges, elegant interactive wizard,
found tracks table, and completion dashboard with zero emojis.
"""

import os
import sys
from typing import Any, Dict, List, Optional

from rich import box
from rich.align import Align
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table
from rich.text import Text

from .config import find_default_config, load_config, save_config

# Force UTF-8 stdout encoding on Windows to prevent legacy charmap crashes
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(legacy_windows=False)


def make_box_badge(text: str, bg_color: str, fg_color: str = "white", width: Optional[int] = None) -> Text:
    """Builds a complete solid colored box with centered text (no brackets)."""
    if width and width > len(text):
        total_pad = width - len(text)
        left_pad = total_pad // 2
        right_pad = total_pad - left_pad
        label = f"{' ' * left_pad}{text}{' ' * right_pad}"
    else:
        label = f"  {text}  "
    return Text(label, style=f"bold {fg_color} on {bg_color}")


def render_gradient_banner() -> Panel:
    """Builds a crisp, left-aligned, two-tone gradient ASCII banner with solid box badges."""
    banner_lines = [
        r"███████╗███████╗██████╗        ██████╗███████╗██╗   ██╗",
        r"╚══███╔╝██╔════╝██╔══██╗      ██╔════╝██╔════╝██║   ██║",
        r"   ███║ ███████╗██║  ██║█████╗██║     ███████╗██║   ██║",
        r"   ███║ ╚════██║██║  ██║╚════╝██║     ╚════██║╚██╗ ██╔╝",
        r"██████║ ███████║██████╔╝      ╚██████╗███████║ ╚████╔╝ ",
        r"╚═════╝ ╚══════╝╚═════╝        ╚═════╝╚══════╝  ╚═══╝  ",
    ]

    ascii_text = Text()
    for line in banner_lines:
        ascii_text.append(line[:24], style="bold #00f0ff")
        ascii_text.append(line[24:30], style="bold bright_white")
        ascii_text.append(line[30:], style="bold #d946ef")
        ascii_text.append("\n")

    sub_text = Text()
    sub_text.append("JioSaavn Downloader with CSV", style="bold bright_white")
    sub_text.append("  |  ", style="bold #facc15")
    sub_text.append("v1.0.0", style="bold bright_cyan")

    badges_text = Text()
    if console.width >= 95:
        items = [
            ("  320 KBPS  ", "bold white on #0284c7"),
            ("  YT MUSIC FALLBACK  ", "bold white on #7c3aed"),
            ("  CSV BATCH  ", "bold white on #059669"),
            ("  ID3 + ART  ", "bold white on #d97706"),
            ("  FULL LYRICS  ", "bold white on #e11d48"),
        ]
        sep = "   "
    else:
        items = [
            (" 320 KBPS ", "bold white on #0284c7"),
            (" YT MUSIC ", "bold white on #7c3aed"),
            (" CSV BATCH ", "bold white on #059669"),
            (" ID3 + ART ", "bold white on #d97706"),
            (" LYRICS ", "bold white on #e11d48"),
        ]
        sep = "  "

    for idx, (label, style) in enumerate(items):
        if idx > 0:
            badges_text.append(sep, style="default")
        badges_text.append(label, style=style)

    banner_group = Group(
        ascii_text,
        sub_text,
        Text(""),
        badges_text,
    )

    return Panel(
        banner_group,
        box=box.ROUNDED,
        border_style="bright_blue",
        padding=(1, 3 if console.width >= 95 else 2),
    )


def print_banner() -> None:
    """Renders the sleek JSD-CSV banner in full color with decent spacing."""
    console.print()
    console.print(render_gradient_banner())
    console.print()


def render_step_header(
    step_num: str,
    title: str,
    subtitle: str = "",
    badge: Optional[str] = None,
    badge_color: str = "#10b981",
) -> None:
    """Renders an elegant, spacious step card header with solid box step badge."""
    console.print()
    step_box = Text(f"  STEP {step_num}  ", style="bold white on #6366f1")
    header = Text()
    header.append_text(step_box)
    header.append("  ")
    header.append(title, style="bold bright_white")
    if badge:
        header.append("  ")
        header.append(f"  {badge}  ", style=f"bold white on {badge_color}")
    console.print(header)
    if subtitle:
        console.print(f"            [dim #94a3b8]{subtitle}[/dim #94a3b8]")
    console.print()


def prompt_interactive_options(
    existing_config: Optional[Dict[str, Any]] = None,
    config_filename: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs the sleek interactive setup wizard with solid box badges, generous padding, and elegant spacing.
    Supports pre-filling defaults from an existing config profile, one-click execution, and saving profiles.
    Returns a dictionary of parsed options.
    """
    wizard_panel = Panel(
        Text.from_markup(
            "[bold bright_white]INTERACTIVE CONFIGURATION WIZARD[/bold bright_white]\n"
            "[dim #94a3b8]Configure your download parameters below or press Enter to accept recommended defaults.[/dim #94a3b8]"
        ),
        box=box.ROUNDED,
        border_style="bold #38bdf8",
        padding=(1, 3),
    )
    console.print(wizard_panel)

    cfg = existing_config
    if not cfg:
        found_cfg_file = find_default_config()
        if found_cfg_file:
            try:
                cfg = load_config(found_cfg_file)
                config_filename = found_cfg_file
            except Exception:
                cfg = None

    if cfg:
        src_label = os.path.basename(config_filename) if config_filename else "preset"
        render_step_header(
            step_num="0",
            title="Saved Configuration Profile Found",
            subtitle=f"Detected existing settings profile '{src_label}'",
            badge="PROFILE",
            badge_color="#7c3aed",
        )
        grid = Table.grid(padding=(0, 3))
        grid.add_column(style="bold cyan", width=16)
        grid.add_column(style="bright_white")
        if cfg.get("url"):
            grid.add_row("URL / Query:", str(cfg.get("url")))
        if cfg.get("csv"):
            grid.add_row("CSV Batch:", str(cfg.get("csv")))
        grid.add_row("Output Folder:", str(cfg.get("output", "./downloads")))
        grid.add_row("Mode / Quality:", f"{cfg.get('mode', 'all')} @ {cfg.get('quality', '320')} kbps")
        grid.add_row("Source / Tagging:", f"{cfg.get('source', 'auto')} (Lyrics: {'Yes' if cfg.get('lyrics', True) else 'No'})")
        grid.add_row("Template:", str(cfg.get("template", "{artist} - {title}")))
        console.print(Panel(grid, box=box.ROUNDED, border_style="#7c3aed", padding=(1, 3)))
        console.print()
        if Confirm.ask("  [bold #00f0ff]>[/] [bold white]Run directly with these saved settings?[/bold white]", default=True):
            console.print("    [bold green]Proceeding with saved settings profile.[/bold green]\n")
            return cfg
        else:
            console.print("    [dim]Starting wizard using saved profile values as defaults.[/dim]\n")

    cfg_data = cfg or {}

    # Step 1: Optional CSV
    render_step_header(
        step_num="1",
        title="CSV Batch Import",
        subtitle="Load tracks directly from an existing CSV file or online URL",
        badge="OPTIONAL",
        badge_color="#475569",
    )
    csv_input = Prompt.ask(
        "  [bold #00f0ff]>[/] [bold white]CSV File Path or Online URL[/bold white] [dim](press Enter to skip)[/dim]",
        default=str(cfg_data.get("csv") or ""),
    ).strip().strip("'\"")

    url_input = ""
    if not csv_input:
        # Step 2: JioSaavn Link or Query
        render_step_header(
            step_num="2",
            title="JioSaavn Link or Search Query",
            subtitle="Song, Album, Playlist, Artist link or free-text search keywords",
        )
        default_url = str(cfg_data.get("url") or "")
        while True:
            url_input = Prompt.ask(
                "  [bold #00f0ff]>[/] [bold white]JioSaavn URL or Search Keywords[/bold white]",
                default=default_url,
            )
            if url_input.strip():
                break
            console.print("    [bold red]Input cannot be empty. Please enter a valid link, query, or CSV path.[/bold red]\n")

        clean_url = url_input.strip().strip("'\"")
        if clean_url.lower().endswith(".csv") or ".csv?" in clean_url.lower() or (os.path.exists(clean_url) and os.path.isfile(clean_url)):
            csv_input = clean_url
            url_input = ""

    # Step 3: Output Directory
    render_step_header(
        step_num="3",
        title="Output Directory",
        subtitle="Target folder where downloaded MP3s and metadata CSV will be stored",
    )
    out_dir = Prompt.ask(
        "  [bold #00f0ff]>[/] [bold white]Destination Folder[/bold white]",
        default=str(cfg_data.get("output") or "./downloads"),
    )

    # Step 4: Mode Selection
    render_step_header(
        step_num="4",
        title="Operational Mode",
        subtitle="Select audio downloading and CSV archival target",
    )
    console.print("    [bold white on #0284c7]  1  [/]  [bold bright_white]Both[/]         [dim]Download MP3s + Export/Update CSV Metadata[/]   [bold white on #16a34a]  RECOMMENDED  [/]")
    console.print("    [bold white on #475569]  2  [/]  [bold bright_white]Songs Only[/]   [dim]Download MP3 audio tracks without creating CSV[/]")
    console.print("    [bold white on #475569]  3  [/]  [bold bright_white]CSV Only[/]     [dim]Fast metadata sync to CSV without downloading audio[/]")
    console.print()
    def_mode_choice = {"all": "1", "songs": "2", "csv": "3"}.get(cfg_data.get("mode", "all"), "1")
    mode_choice = Prompt.ask(
        "  [bold #00f0ff]>[/] [bold white]Choose Mode [1-3][/bold white]",
        choices=["1", "2", "3"],
        default=def_mode_choice,
    )
    mode_map = {"1": "all", "2": "songs", "3": "csv"}
    selected_mode = mode_map[mode_choice]

    # Step 5: Audio Quality (if downloading songs)
    selected_quality = str(cfg_data.get("quality", "320"))
    if selected_mode in ("all", "songs"):
        render_step_header(
            step_num="5",
            title="Target Audio Bitrate",
            subtitle="Audio stream bitrate and MP3 transcoding fidelity",
        )
        console.print("    [bold white on #0284c7]  1  [/]  [bold #4ade80]320 kbps[/]     [dim]Maximum Studio Fidelity (CBR 320k)[/]   [bold white on #16a34a]  MAXIMUM  [/]")
        console.print("    [bold white on #475569]  2  [/]  [bold #38bdf8]160 kbps[/]     [dim]High Quality Standard (CBR 160k)[/]")
        console.print("    [bold white on #475569]  3  [/]  [bold #fbbf24]96 kbps[/]      [dim]Bandwidth Saver (CBR 96k)[/]")
        console.print()
        def_q_choice = {"320": "1", "160": "2", "96": "3"}.get(str(cfg_data.get("quality", "320")), "1")
        q_choice = Prompt.ask(
            "  [bold #00f0ff]>[/] [bold white]Choose Bitrate [1-3][/bold white]",
            choices=["1", "2", "3"],
            default=def_q_choice,
        )
        q_map = {"1": "320", "2": "160", "3": "96"}
        selected_quality = q_map[q_choice]

    # Step 6: Audio Stream Source
    selected_source = str(cfg_data.get("source", "auto"))
    if selected_mode in ("all", "songs"):
        render_step_header(
            step_num="6",
            title="Audio Stream Engine",
            subtitle="Primary audio provider and automatic fallback strategy",
        )
        console.print("    [bold white on #0284c7]  1  [/]  [bold #c084fc]Auto[/]            [dim]JioSaavn CDN stream + YT Music fallback[/]   [bold white on #7c3aed]  DUAL ENGINE  [/]")
        console.print("    [bold white on #475569]  2  [/]  [bold #38bdf8]JioSaavn Direct[/] [dim]Raw master audio stream directly from Saavn CDN[/]")
        console.print("    [bold white on #475569]  3  [/]  [bold #f87171]YouTube Music[/]   [dim]Matched audio stream via YouTube Music[/]")
        console.print()
        def_src_choice = {"auto": "1", "saavn": "2", "ytmusic": "3"}.get(str(cfg_data.get("source", "auto")), "1")
        src_choice = Prompt.ask(
            "  [bold #00f0ff]>[/] [bold white]Choose Engine [1-3][/bold white]",
            choices=["1", "2", "3"],
            default=def_src_choice,
        )
        src_map = {"1": "auto", "2": "saavn", "3": "ytmusic"}
        selected_source = src_map[src_choice]

    # Step 7: Filename Template
    render_step_header(
        step_num="7",
        title="Custom Filename Pattern",
        subtitle="Tags: {artists}, {artist}, {album_artist}, {title}, {album}, {year}, {track}, {date}, {genre}...",
    )
    template = Prompt.ask(
        "  [bold #00f0ff]>[/] [bold white]Filename Pattern[/bold white]",
        default=str(cfg_data.get("template") or "{artist} - {title}"),
    )

    # Determine default artist separator choice from existing config
    cur_sep = str(cfg_data.get("artists_separator") if cfg_data.get("artists_separator") is not None else ", ")
    if cur_sep in (", ", ","):
        def_sep = "1"
    elif cur_sep in ("/", " / "):
        def_sep = "2"
    elif cur_sep in ("&", " & "):
        def_sep = "3"
    elif cur_sep in ("|", " | "):
        def_sep = "4"
    else:
        def_sep = "5"

    artists_sep = cur_sep
    if any(tag in template.lower() for tag in ("{artists}", "{all_artists}", "{allartists}")):
        console.print()
        console.print("    [bold #38bdf8]Artists Tag Separator for {artists}:[/bold #38bdf8]")
        console.print("    [bold white on #0284c7]  1  [/]  [bold #4ade80]', '[/]     [dim]Comma-space  (e.g. Pritam, Arijit Singh)[/]     [bold white on #16a34a]  DEFAULT  [/]")
        console.print("    [bold white on #475569]  2  [/]  [bold #38bdf8]'/'[/]      [dim]Slash        (e.g. Pritam / Arijit Singh)[/]")
        console.print("    [bold white on #475569]  3  [/]  [bold #c084fc]' & '[/]    [dim]Ampersand    (e.g. Pritam & Arijit Singh)[/]")
        console.print("    [bold white on #475569]  4  [/]  [bold #fbbf24]' | '[/]    [dim]Pipe         (e.g. Pritam | Arijit Singh)[/]")
        console.print("    [bold white on #475569]  5  [/]  [bold #f87171]Custom[/]   [dim]Enter your own custom separator string[/]")
        console.print()
        sep_choice = Prompt.ask(
            "  [bold #00f0ff]>[/] [bold white]Choose Separator [1-5][/bold white]",
            choices=["1", "2", "3", "4", "5", ", ", "/", " / ", "&", " & ", "|", " | "],
            default=def_sep,
        )
        if sep_choice in ("1", ", "):
            artists_sep = ", "
        elif sep_choice in ("2", "/", " / "):
            artists_sep = "/" if sep_choice == "/" else " / "
        elif sep_choice in ("3", "&", " & "):
            artists_sep = " & "
        elif sep_choice in ("4", "|", " | "):
            artists_sep = "|" if sep_choice == "|" else " | "
        else:
            artists_sep = Prompt.ask(
                "  [bold #00f0ff]>[/] [bold white]Enter Custom Separator[/bold white]",
                default=cur_sep if cur_sep not in (", ", "/", " / ", " & ", " | ", "|") else ", ",
            )

    # Step 8: Lyrics
    render_step_header(
        step_num="8",
        title="ID3 Tagging & Lyrics",
        subtitle="Embed synchronized or full lyrics into MP3 ID3v2 USLT frames",
    )
    fetch_lyrics = Confirm.ask(
        "  [bold #00f0ff]>[/] [bold white]Fetch and embed full lyrics into MP3 tags?[/bold white]",
        default=bool(cfg_data.get("lyrics", True)),
    )

    # Step 9: Cookies file
    render_step_header(
        step_num="9",
        title="YouTube Music Cookies",
        subtitle="Provide cookies.txt path for bot detection bypass & premium account audio",
        badge="OPTIONAL",
        badge_color="#475569",
    )
    cookies_input = Prompt.ask(
        "  [bold #00f0ff]>[/] [bold white]Path to cookies.txt[/bold white] [dim](press Enter to skip)[/dim]",
        default=str(cfg_data.get("cookies") or ""),
    )
    cookies_path = cookies_input.strip() if cookies_input.strip() and os.path.exists(cookies_input.strip()) else None

    # Step 10: Save configuration profile
    render_step_header(
        step_num="10",
        title="Save Settings Profile",
        subtitle="Save these parameters to a JSON config file to edit and rerun without retyping",
        badge="OPTIONAL",
        badge_color="#475569",
    )
    save_cfg_confirm = Confirm.ask(
        "  [bold #00f0ff]>[/] [bold white]Save current settings to a config file?[/bold white]",
        default=False,
    )
    if save_cfg_confirm:
        save_path = Prompt.ask(
            "  [bold #00f0ff]>[/] [bold white]Config file path or name[/bold white]",
            default=config_filename or "config.json",
        ).strip() or "config.json"
        saved_file = save_config({
            "url": url_input.strip(),
            "csv": csv_input.strip(),
            "output": out_dir.strip(),
            "mode": selected_mode,
            "quality": selected_quality,
            "source": selected_source,
            "template": template.strip(),
            "artists_separator": artists_sep,
            "lyrics": fetch_lyrics,
            "cover": True,
            "cookies": cookies_path,
            "id3_version": int(cfg_data.get("id3_version", 4)),
        }, save_path)
        console.print(f"    [bold green]Settings profile saved to:[/] [bold cyan]{saved_file}[/bold cyan]")
        console.print(f"    [dim]You can edit this file in any text editor and rerun anytime with:[/] [bold #38bdf8]python main.py -C {save_path}[/bold #38bdf8]\n")

    console.print()
    return {
        "url": url_input.strip(),
        "csv": csv_input.strip(),
        "output": out_dir.strip(),
        "mode": selected_mode,
        "quality": selected_quality,
        "source": selected_source,
        "template": template.strip(),
        "artists_separator": artists_sep,
        "lyrics": fetch_lyrics,
        "cookies": cookies_path,
        "cover": True,
        "id3_version": int(cfg_data.get("id3_version", 4)),
    }


def display_collection_header(meta: Dict[str, Any]) -> None:
    """Displays collection header details before track listing with solid box badges and generous padding."""
    raw_type = meta.get("type", "Collection").lower()
    title = meta.get("title", "Unknown")
    artist = meta.get("artist", "")
    count = meta.get("count", 0)
    source = meta.get("source", "")

    header_text = Text()

    # Complete solid boxes for collection types (no brackets)
    type_badge_map = {
        "csv": ("  CSV BATCH  ", "bold white on #059669"),
        "album": ("  ALBUM  ", "bold white on #2563eb"),
        "playlist": ("  PLAYLIST  ", "bold white on #7c3aed"),
        "artist": ("  ARTIST TOP  ", "bold white on #d97706"),
        "song": ("  SINGLE  ", "bold white on #db2777"),
        "search": ("  SEARCH RESULTS  ", "bold white on #0891b2"),
    }
    badge_label, badge_style = type_badge_map.get(raw_type, ("  COLLECTION  ", "bold white on #4b5563"))
    header_text.append(badge_label, style=badge_style)
    header_text.append("   ")
    header_text.append(title, style="bold bright_white")

    if artist and raw_type != "csv":
        header_text.append("   |   ", style="dim yellow")
        header_text.append("Artist: ", style="bold cyan")
        header_text.append(artist, style="bright_white")

    if source and raw_type == "csv":
        header_text.append("   |   ", style="dim yellow")
        header_text.append("Source: ", style="bold cyan")
        short_src = source if len(source) <= 50 else source[:47] + "..."
        header_text.append(short_src, style="dim white")

    header_text.append("   |   ", style="dim yellow")
    header_text.append(f"  {count} TRACKS  ", style="bold black on #4ade80")

    console.print()
    console.print(Panel(header_text, box=box.ROUNDED, border_style="bright_blue", padding=(1, 3)))
    console.print()


def display_tracks_table(songs: List[Dict[str, Any]], max_rows: int = 25) -> None:
    """Displays a neat, responsive table of tracks about to be processed with solid box badges."""
    has_year = console.width >= 105

    table = Table(
        title="[bold #38bdf8]=== Found Tracks Preview ===[/bold #38bdf8]",
        title_justify="left",
        box=box.ROUNDED,
        border_style="bright_blue",
        header_style="bold #c084fc",
        padding=(0, 1),
        expand=True,
    )
    table.add_column("#", style="dim cyan", width=3, justify="right", no_wrap=True)
    table.add_column("Title", style="bold bright_white", ratio=3, no_wrap=True, overflow="ellipsis")
    table.add_column("Artist(s)", style="bold #38bdf8", ratio=2, no_wrap=True, overflow="ellipsis")
    table.add_column("Album", style="bold #facc15", ratio=2, no_wrap=True, overflow="ellipsis")
    if has_year:
        table.add_column("Year", style="bold #fbbf24", width=6, justify="center", no_wrap=True)
    table.add_column("Duration", style="bold #4ade80", width=8, justify="center", no_wrap=True)
    table.add_column(Align.center("Lyrics"), width=12, no_wrap=True)

    display_list = songs[:max_rows]
    for idx, s in enumerate(display_list):
        if s.get("has_lyrics") or s.get("lyrics"):
            lyrics_cell = Align.center(Text("  LYRICS  ", style="bold white on #16a34a"))
        else:
            lyrics_cell = Align.center(Text("--", style="dim #f472b6"))
        dur_fmt = s.get("duration_formatted", "00:00")
        row = [
            f"{s.get('track_number') or idx + 1:02d}",
            s.get("title", "Unknown"),
            s.get("artists") or s.get("primary_artists") or s.get("artist") or "Unknown",
            s.get("album", "Unknown"),
        ]
        if has_year:
            row.append(str(s.get("year") or "--"))
        row.extend([dur_fmt, lyrics_cell])
        table.add_row(*row)

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
    """Renders a sleek, colorful dashboard summary card with consistent-width solid boxes and generous spacing."""
    def make_badge(text: str, bg: str, width: int = 14) -> str:
        total_pad = max(0, width - len(text))
        left_pad = total_pad // 2
        right_pad = total_pad - left_pad
        label = f"{' ' * left_pad}{text}{' ' * right_pad}"
        return f"[bold white on {bg}]{label}[/]"

    summary_table = Table.grid(padding=(0, 4))
    summary_table.add_column(justify="left")
    summary_table.add_column(style="bright_white")

    summary_table.add_row(
        make_badge("COMPLETE", "#16a34a", 14),
        f"[bold bright_green]{success_count}[/] / [bold bright_white]{total}[/] tracks successfully processed",
    )
    if failed_count > 0:
        summary_table.add_row(
            make_badge("FAILED", "#dc2626", 14),
            f"[bold red]{failed_count}[/] tracks encountered errors or skipped",
        )
    summary_table.add_row(
        make_badge("OUTPUT", "#0284c7", 14),
        f"[bold bright_cyan]{os.path.abspath(output_dir)}[/bold bright_cyan]",
    )
    if csv_path and os.path.exists(csv_path):
        summary_table.add_row(
            make_badge("CSV RECORD", "#7c3aed", 14),
            f"[bold bright_magenta]{os.path.abspath(csv_path)}[/bold bright_magenta]",
        )
    mins, secs = divmod(int(elapsed_seconds), 60)
    summary_table.add_row(
        make_badge("TIME", "#d97706", 14),
        f"[bold #facc15]{mins}m {secs:02d}s[/bold #facc15]",
    )

    panel = Panel(
        summary_table,
        title="[bold bright_white]JSD-CSV Pipeline Complete[/bold bright_white]",
        box=box.ROUNDED,
        border_style="bright_green",
        padding=(1, 3),
    )
    console.print()
    console.print(panel)
    console.print()


def print_interrupt_message(detail: Optional[str] = None) -> None:
    """Renders a sleek, pleasant exit notification when interrupted via Ctrl+C (no emojis)."""
    console.print()
    badge = Text("  CANCELLED  ", style="bold white on #ef4444")
    content = Text()
    content.append_text(badge)
    content.append("  ")
    content.append("Operation cancelled by user (Ctrl+C). Exiting safely.", style="bold bright_white")
    if detail:
        content.append("\n\n  ")
        content.append(detail, style="dim #94a3b8")

    panel = Panel(
        content,
        box=box.ROUNDED,
        border_style="#ef4444",
        padding=(1, 3),
    )
    console.print(panel)
    console.print()
