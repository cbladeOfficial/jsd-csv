#!/usr/bin/env python3
"""
JSD-CSV: Jio Saavn Downloader - (with) CSV
Executable entrypoint. Run with:
    python main.py [options]
"""

import sys

# Ensure UTF-8 output across all platforms, including Windows Command Prompt and PowerShell
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

from jsd_csv.cli import main

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        try:
            from jsd_csv.ui import print_interrupt_message
            print_interrupt_message()
        except Exception:
            pass
        sys.exit(130)

