# JSD-CSV (Jio Saavn Downloader - with CSV)

```
     ██╗███████╗██████╗         ██████╗███████╗██╗   ██╗
     ██║██╔════╝██╔══██╗       ██╔════╝██╔════╝██║   ██║
     ██║███████╗██║  ██║ █████╗██║     ███████╗██║   ██║
██   ██║╚════██║██║  ██║ ╚════╝██║     ╚════██║╚██╗ ██╔╝
╚█████╔╝███████║██████╔╝       ╚██████╗███████║ ╚████╔╝ 
 ╚════╝ ╚══════╝╚═════╝         ╚═════╝╚══════╝  ╚═══╝  
```

---

## 🌟 Key Features

- **JioSaavn Direct Audio Extraction**: Fetches master audio streams directly from JioSaavn's CDN up to **320 kbps** (with automatic fallback to 160 kbps and 96 kbps).
- **Exact YouTube Music Matching**: Searches YouTube Music for exact track matches using Title, Artist, Album, and Duration tolerance heuristics, calculating a match confidence score.
- **YouTube Music Download Fallback**: If a JioSaavn direct stream is unavailable or geographically restricted, seamlessly falls back to downloading the matched audio from YouTube Music via `yt-dlp`.
- **Rich CSV Metadata Archival & Export**: Automatically exports all track details into an Excel/Google Sheets-friendly CSV file (`utf-8-sig`) saved directly in your output directory.
- **Download Songs Later from CSV**: Import previously generated CSV files (local paths or online HTTP/HTTPS URLs) to download or re-download songs at any time.
- **Complete ID3v2 Tagging**: Automatically embeds Title, Artist(s), Album, Track Number, Year, Genre/Language, Publisher/Label, Copyright, Comment, **Full Lyrics (`USLT`)**, and **Crisp 500x500 Cover Art (`APIC`)** into MP3 files—taking reference from the CSV or resolved on the fly.
- **Customizable Filename Templates**: Format filenames using identifiers like `{Artist} - {Title}`, `{Album}/{Track} - {Title}`, `[{Year}] {Title}`, and more.
- **3 Flexible Operational Modes**:
  1. `all`: Download MP3 songs + Export/Update CSV metadata (Default)
  2. `songs`: Download MP3 songs only (no CSV file)
  3. `csv`: Export CSV metadata only (fast, no audio files downloaded)
- **Sleek Rich Console UI**: Features a modern terminal interface with interactive prompts, collection summary panels, tracklist preview tables, and live multi-progress bars.
- **Cookies Support**: Accepts user-provided `cookies.txt` files for authenticated YouTube Music downloads and bot-check bypassing.

---

## 🛠️ Prerequisites

1. **Python 3.9+** installed on your system.
2. **FFmpeg** installed and accessible in your system's `PATH`:
   - **Windows**: Install via `winget install Gyan.FFmpeg` or download from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/).
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

---

## 🚀 Installation & Executable Build

### Option A: Use the Standalone Windows Executable (.exe)
You can build a standalone single-file `.exe` that does not require Python:

```bash
# Double click build.bat or run:
pyinstaller --noconfirm --clean jsd-csv.spec
```

The resulting executable will be in the **`dist/`** directory:
```
dist/jsd-csv.exe
```

You can move `jsd-csv.exe` anywhere! For complete portability across systems without FFmpeg installed globally, simply place `ffmpeg.exe` in the same directory as `jsd-csv.exe`. JSD-CSV automatically detects and utilizes local FFmpeg binaries next to the executable.

---

### Option B: Python Installation (Source)

Clone or navigate to the repository directory:

```bash
cd jsd-csv
```

Install the required Python packages:

```bash
pip install -r requirements.txt
```

*(Optional)* Install in editable mode to use the `jsd-csv` command anywhere:

```bash
pip install -e .
```

---

## 💻 Usage

JSD-CSV can be run in two ways:
1. **Interactive Mode**: Simple step-by-step wizard when run without parameters.
2. **CLI Switches Mode**: Direct command-line arguments for automated workflows and scripting.

### 1. Interactive Wizard

Simply run the script with no arguments:

```bash
python main.py
```
*(Or `jsd-csv` / `jsd-csv.exe`)*

You will be guided through:
- **Pasting an existing CSV path or online URL** (optional, press Enter to skip and enter a link/query instead).
- Entering a JioSaavn song, album, or playlist URL (or search query).
- Selecting the output folder (default: `./downloads`).
- Choosing the mode: `Songs + CSV`, `Songs only`, or `CSV only`.
- Selecting the audio quality: `320 kbps`, `160 kbps`, or `96 kbps`.
- Choosing audio source preference: `Auto`, `JioSaavn Direct`, or `YouTube Music`.
- Specifying a filename template.
- Toggling lyrics and album cover embedding.
- Providing an optional `cookies.txt` path.

---

### 2. CLI Switches (Power-User Mode)

```bash
python main.py [OPTIONS]
```

#### Common Examples:

- **Download a single song (MP3 + CSV):**
  ```bash
  python main.py -u "https://www.jiosaavn.com/song/kesariya/.../..." -o ./my_music
  ```

- **Download songs from a local CSV file (with ID3 metadata & album art):**
  ```bash
  python main.py -f ./my_music/metadata.csv -o ./downloaded_songs
  ```

- **Download songs from an online CSV URL:**
  ```bash
  python main.py -f "https://raw.githubusercontent.com/user/repo/main/playlist.csv" -o ./songs
  ```

- **Download an entire album with track numbers in filenames:**
  ```bash
  python main.py -u "https://www.jiosaavn.com/album/rockstar/C3Br8V0qKrc_" -t "{track} - {title}" -o ./Rockstar
  ```

- **Download a playlist at 320 kbps with automatic confirmation:**
  ```bash
  python main.py -u "https://www.jiosaavn.com/featured/weekly-top-songs/.../..." -q 320 -y -o ./playlist
  ```

- **Export only CSV metadata (no music files downloaded):**
  ```bash
  python main.py -u "https://www.jiosaavn.com/album/.../..." -m csv -o ./csv_reports
  ```

- **Download audio files only without generating a CSV (embeds tags & cover on the fly):**
  ```bash
  python main.py -u "https://www.jiosaavn.com/song/.../..." -m songs -o ./songs_only
  ```

- **Force download via YouTube Music using cookies:**
  ```bash
  python main.py -u "Kesariya Arijit Singh" -s ytmusic -c ./cookies.txt -o ./yt_downloads
  ```

---

## ⚙️ Command-Line Switches Reference

| Switch | Long Flag | Description | Default |
| :--- | :--- | :--- | :--- |
| `-u` | `--url` | JioSaavn URL (song/album/playlist/artist) or search query | *None* |
| `-f` | `--from-csv`, `--csv-input` | Path or URL to an existing CSV file to download songs from | *None* |
| `-o` | `--output` | Destination output directory | `./downloads` |
| `-m` | `--mode` | Operational mode: `all` (songs + CSV), `songs`, or `csv` | `all` |
| `-t` | `--template` | Filename naming pattern (supports case-insensitive tokens) | `{artist} - {title}` |
| `-q` | `--quality` | Target audio bitrate: `320`, `160`, or `96` kbps | `320` |
| `-s` | `--source` | Audio stream source: `auto`, `saavn`, or `ytmusic` | `auto` |
| `-c` | `--cookies` | Path to Netscape-format `cookies.txt` file for YouTube Music | *None* |
| `-C` | `--config` | Load download settings from a JSON configuration file | *None* |
| | `--save-config` | Save current parameters to a JSON configuration file | `config.json` |
| | `--id3-version` | ID3v2 tag version to write: `4` (native multi-artist) or `3` (legacy) | `4` |
| | `--lyrics` / `--no-lyrics` | Enable or disable full lyrics retrieval and embedding | Enabled |
| | `--cover` / `--no-cover` | Enable or disable high-resolution album cover embedding | Enabled |
| | `--csv-name` | Custom name for the generated CSV metadata file | *Collection title* |
| `-y` | `--yes` | Skip interactive download confirmation prompt | `False` |
| `-i` | `--interactive` | Force interactive wizard | `False` |
| `-v` | `--version` | Display program version | |
| `-h` | `--help` | Show complete command help | |

---

## 🏷️ Filename Template Placeholders

Identifiers are **case-insensitive** and automatically sanitized for Windows, Linux, and macOS:

| Identifier | Description | Example |
| :--- | :--- | :--- |
| `{title}` | Song title | `Kesariya` |
| `{artist}` | Primary artist name | `Arijit Singh` |
| `{artists}` | All credited artists (comma-separated) | `Arijit Singh, Pritam` |
| `{album}` | Album name | `Brahmastra` |
| `{year}` | Release year | `2022` |
| `{track}` | Zero-padded track number | `01`, `02`, `10` |
| `{track_number}` | Raw track number | `1`, `2`, `10` |
| `{duration}` | Formatted duration with hyphens | `04-28` |
| `{language}` | Song language | `Hindi` |
| `{id}` | JioSaavn track ID | `rjkrTnma` |

**Template Examples:**
- `{artist} - {title}` &rarr; `Arijit Singh - Kesariya.mp3`
- `{album}/{track} - {title}` &rarr; `Brahmastra/01 - Kesariya.mp3`
- `[{year}] {artists} - {title}` &rarr; `[2022] Arijit Singh, Pritam - Kesariya.mp3`

---

## 📊 CSV Metadata Schema

The generated CSV file contains 27 comprehensive fields encoded in `utf-8-sig` *(Note: Multi-line Full Lyrics are cleanly embedded directly into the MP3 ID3 tags (`USLT`) rather than bloating the CSV spreadsheet)*:

| Column | Description |
| :--- | :--- |
| `Track Number` | Track order index in the collection |
| `Title` | Unescaped song title |
| `Artists` | Deduplicated essential track artists (singers & featured; excluding movie cast) |
| `Album Artist` | Album artist or primary music composer |
| `Primary Artist` | Lead vocalist or composer |
| `Album` | Album or soundtrack title |
| `Year` | Release year |
| `Release Date` | Full release date (YYYY-MM-DD) |
| `Duration (Formatted)` | Formatted duration (`MM:SS`) |
| `Duration (Seconds)` | Exact track duration in seconds |
| `Bitrate` | Selected audio stream quality (e.g. 320 kbps) |
| `Language` | Primary audio language |
| `Record Label` | Recording label / publisher |
| `Copyright` | Official copyright line |
| `JioSaavn ID` | JioSaavn unique song identifier |
| `JioSaavn URL` | Canonical JioSaavn web URL |
| `Album Art URL` | Direct link to high-resolution 500x500 cover art |
| `Has Lyrics` | `Yes` or `No` |
| `Lyrics Snippet` | Short teaser lyrics |
| `YT Music Title` | Matched YouTube Music track title |
| `YT Music Video ID` | Matched YouTube video ID |
| `YT Music URL` | Direct YouTube Music stream URL |
| `YT Match Score (%)` | Algorithmic match confidence percentage |
| `Audio Source` | Source used (`JioSaavn CDN` or `YouTube Music`) |
| `Filename` | Local sanitized filename |
| `File Path` | Absolute path to the saved MP3 file |
| `Download Status` | Status: `Downloaded`, `CSV Only`, or `Failed` |

---

## 💾 Configuration Profiles (`config.json`)

To avoid re-typing parameters every time, you can save your inputs into a JSON profile, edit it directly in any text editor, and re-run with one command:

```bash
# Save your current parameters into config.json
python main.py -u "Kesariya" -o ./my_music -q 320 --save-config config.json

# Run directly from the configuration file
python main.py -C config.json

# Skip confirmation and run immediately
python main.py -C config.json -y
```

Example `config.json`:
```json
{
    "url": "https://www.jiosaavn.com/album/rockstar/C3Br8V0qKrc_",
    "csv": "",
    "output": "./downloads",
    "mode": "all",
    "quality": "320",
    "source": "auto",
    "template": "{track} - {title}",
    "lyrics": true,
    "cover": true,
    "cookies": null,
    "id3_version": 4
}
```

When running in interactive wizard mode, JSD-CSV automatically detects any existing `config.json` in the current folder, displays a summary card, and asks if you'd like to run directly or use it as defaults.

---

## 🎵 Multi-Artist Tagging & Media Player Support

JSD-CSV ensures collaborating artists are separated into distinct discrete entities rather than lumped into a single comma-separated text string:

- **ID3v2.4 Null Separation (`TPE1`)**: Multiple track artists (singers, featured artists) are stored as discrete strings separated by null bytes (`\x00`), allowing modern players (**foobar2000**, **MusicBee**, **Plex**, **Kodi**, **Navidrome**, **Poweramp**) to index each artist under their individual library pages.
- **Dedicated User Frames (`TXXX:ARTISTS` & `TXXX:Artists`)**: Compatible with **MusicBrainz Picard**, **Mp3tag**, and advanced tagging engines.
- **Album Artist Separation (`TPE2` & `TXXX:ALBUMARTISTS`)**: Preserves the primary album composer/artist, preventing collaborative tracks from fracturing your album into multiple fragmented entries.

---

## 🍪 How to Use a `cookies.txt` File

If you experience YouTube Music rate limiting or bot verification prompts during fallback matching:

1. Install a browser extension like **Get cookies.txt LOCALLY** (Chrome/Firefox).
2. Navigate to [music.youtube.com](https://music.youtube.com).
3. Export your cookies in standard Netscape format and save as `cookies.txt`.
4. Pass the file via the `-c` switch:
   ```bash
   python main.py -u "..." -c ./cookies.txt
   ```

---

## ⚖️ License

This project is released under the **MIT License**.
