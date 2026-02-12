# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Lazy Typer is a Python CLI tool that simulates human typing at ~250 WPM with natural variation (±45%). Designed for typing text into Word, Excel, or as compressed single-line output when copy-paste isn't available (e.g., Windows VMs on macOS).

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the tool
python lazy_typer.py
```

## Architecture

Single-file application (`lazy_typer.py`) with these sections:

- **Colors class**: ANSI color codes for terminal output styling
- **Configuration constants**: WPM (250), VARIATION (0.45), DEFAULT_COUNTDOWN (5), VERSION, GITHUB_REPO
- **`clean_text()`**: Text preprocessor — normalizes smart quotes to straight quotes, converts Unicode bullets to dashes, removes tabs, converts separator lines, fixes list spacing, preserves paragraph breaks
- **`type_text()`**: Core typing loop using pyautogui with per-character delays and paragraph break handling
- **`type_newline()`**: Mode-aware newline handling (Enter for Word, Alt+Enter for Excel)
- **`get_multiline_input()`**: Multi-line text input that terminates on first empty line
- **Version check system**: `check_and_prompt_update()` → `check_for_latest_version()` → `arrow_key_select()` → `run_git_pull()`
- **`main()`**: Startup flow: version check → header → mode selection → countdown → typing loop

## Application Modes

- **Word**: Standard Enter key for newlines
- **Excel**: Alt+Enter for in-cell line breaks
- **Compress**: All text on single line, no line breaks

## Key Implementation Details

- `pyautogui.PAUSE = 0` disables the default 0.1s pause after each pyautogui call (critical for speed)
- `pyautogui.FAILSAFE = False` prevents corner-trigger interrupts
- Separator lines (---, ===, ⸻) convert to Enter presses, not typed text
- Text input terminates on a single empty line (2 Enter presses: one to end text, one blank to confirm)
- Single blank lines are preserved as paragraph breaks in typed output
- Smart quotes (`'`, `'`, `"`, `"`) normalized to straight quotes before typing
- Unicode bullet characters (`•`, `●`, `◦`, etc.) converted to dashes
- Bullet/numbered lists preserved with proper spacing

## Gotchas

- **Input terminates on first empty line** in `get_multiline_input()` — blank lines in pasted text will end input early, so paragraph breaks are not preserved
- **curl not urllib**: Version check uses `curl` via subprocess because Python 3.13 on macOS has SSL certificate verification failures with `urllib.request`
- **`__pycache__` clearing**: Auto-update runs `shutil.rmtree(__pycache__)` before `os.execv()` restart to prevent stale bytecode from caching the old VERSION
- **Header box width**: The print_header() box uses fixed-width lines (55 visible chars between `║` delimiters). When changing header text, count visible characters excluding ANSI escape codes
- **VERSION management**: Always update all three locations: `VERSION` constant in `lazy_typer.py`, README badge, and GitHub release (`gh release create`)
- **Arrow key input**: `arrow_key_select()` uses `tty.setcbreak()` + `os.read()` with 50ms `select.select()` timeout to distinguish Escape from arrow sequences. Falls back to numbered input if not a TTY
