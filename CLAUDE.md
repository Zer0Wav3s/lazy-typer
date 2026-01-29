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

Single-file application (`lazy_typer.py`) with these key components:

- **Colors class**: ANSI color codes for terminal output styling
- **Configuration constants**: WPM (250), VARIATION (0.45), COUNTDOWN_SECONDS (5)
- **`calculate_delay()`**: Randomized delay generator for human-like typing cadence
- **`clean_text()`**: Text preprocessor that removes tabs, converts separator lines, fixes list spacing
- **`type_text()`**: Core typing loop using pyautogui with per-character delays
- **`type_newline()`**: Mode-aware newline handling (Enter for Word, Alt+Enter for Excel)
- **`main()`**: Interactive loop with mode selection and text input

## Application Modes

- **Word**: Standard Enter key for newlines
- **Excel**: Alt+Enter for in-cell line breaks
- **Compress**: All text on single line, no line breaks

## Key Implementation Details

- `pyautogui.PAUSE = 0` disables the default 0.1s pause after each pyautogui call (critical for speed)
- `pyautogui.FAILSAFE = False` prevents corner-trigger interrupts
- Separator lines (---, ===, ⸻) convert to Enter presses, not typed text
- Text input terminates on one empty line (two Enter presses)
- Bullet/numbered lists preserved with proper spacing
