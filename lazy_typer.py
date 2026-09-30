#!/usr/bin/env python3
"""
Lazy Typer - Simulates human typing at ~250 WPM with natural variation.
Supports Word, Excel, and Compress modes. Works with Windows VMs on macOS.
"""

import time
import random
import sys
import re
import os
import shutil
import subprocess
import json
import csv
import io
import unicodedata
import argparse
import pyautogui

# ═══════════════════════════════════════════════════════════════════════════════
# TERMINAL COLORS
# ═══════════════════════════════════════════════════════════════════════════════

class Colors:
    """ANSI color codes for terminal output."""
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'

    # Colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Backgrounds
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'


def print_header():
    """Print the application header."""
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET}  {Colors.YELLOW}{Colors.BOLD}LAZY TYPER{Colors.RESET} {Colors.DIM}v{VERSION}{Colors.RESET}  {Colors.GRAY}- Human-like typing simulator     {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}║{Colors.RESET}  {Colors.GRAY}Speed: ~{WPM} WPM with natural variation               {Colors.CYAN}{Colors.BOLD}║{Colors.RESET}")
    print(f"{Colors.CYAN}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
    print()


def print_success(message: str):
    """Print a success message."""
    print(f"{Colors.GREEN}{Colors.BOLD}✓{Colors.RESET} {Colors.GREEN}{message}{Colors.RESET}")


def print_info(message: str):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {message}")


def print_warning(message: str):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {Colors.YELLOW}{message}{Colors.RESET}")


def print_error(message: str):
    """Print an error message."""
    print(f"{Colors.RED}✗{Colors.RESET} {Colors.RED}{message}{Colors.RESET}")


def print_divider():
    """Print a visual divider."""
    print(f"{Colors.GRAY}{'─' * 56}{Colors.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

# CRITICAL: Disable pyautogui's default pause (0.1 sec after each call)
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# Typing configuration
WPM = 250
CHARS_PER_WORD = 5
VARIATION = 0.45  # ±45% randomness for more natural feel
WORD_PAUSE_MULTIPLIER = 1.08
DEFAULT_COUNTDOWN = 5

# Version and update check
VERSION = "1.4.0"
GITHUB_REPO = "Zer0Wav3s/lazy-typer"

# Calculate base delay
BASE_DELAY = 60.0 / (WPM * CHARS_PER_WORD)

# Special marker for separator-based line breaks
SEPARATOR_MARKER = '\x00SEP\x00'

# Human-readable mode names, shared by every place that displays one
MODE_DISPLAY = {
    "word": "Word",
    "excel": "Excel - Single Cell",
    "table": "Excel - Table / Grid",
    "text": "Plain Text",
    "sql": "SQL / Code",
    "compress": "Compress",
}


# ═══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_delay(is_word_boundary: bool = False) -> float:
    """Calculate a randomized delay for human-like typing."""
    delay = BASE_DELAY * random.uniform(1 - VARIATION, 1 + VARIATION)
    if is_word_boundary:
        delay *= WORD_PAUSE_MULTIPLIER
    return delay


def type_string(text: str):
    """Type a string with human-like delays, handling Unicode via clipboard paste.

    ASCII characters are typed one at a time via pyautogui.
    Consecutive non-ASCII characters are batched into a single clipboard paste
    to avoid Command key bleed-through issues.
    """
    i = 0
    while i < len(text):
        if text[i].isascii():
            pyautogui.write(text[i], interval=0)
            time.sleep(calculate_delay(is_word_boundary=(text[i] == ' ')))
            i += 1
        else:
            # Batch consecutive non-ASCII characters into one paste
            start = i
            while i < len(text) and not text[i].isascii():
                i += 1
            batch = text[start:i]
            if not paste_via_clipboard(batch):
                # Clipboard unusable: type the closest ASCII instead of
                # pasting whatever happens to be on it
                for c in to_ascii(batch)[0]:
                    pyautogui.write(c, interval=0)
                    time.sleep(calculate_delay())
                continue
            # Simulate natural typing delay for the batch length
            for _ in range(len(batch) - 1):
                time.sleep(calculate_delay())


def paste_via_clipboard(batch: str) -> bool:
    """Paste batch with Cmd+V, then put the user's clipboard back.

    Returns False without pasting if the clipboard can't be read or our write
    never shows up on it: pressing Cmd+V then would paste the user's own
    clipboard contents into the document.
    """
    try:
        saved_clipboard = subprocess.run(
            ['pbpaste'], capture_output=True, check=True, timeout=2
        ).stdout
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False  # can't save it, so don't overwrite it

    batch_bytes = batch.encode('utf-8')
    try:
        subprocess.run(['pbcopy'], input=batch_bytes, check=True, timeout=2)
        # Poll pbpaste until the clipboard actually reflects our batch —
        # pbcopy can return before the pasteboard server has committed.
        deadline = time.monotonic() + 1.0
        confirmed = False
        while time.monotonic() < deadline:
            current = subprocess.run(['pbpaste'], capture_output=True, timeout=2).stdout
            if current == batch_bytes:
                confirmed = True
                break
            time.sleep(0.01)
        if not confirmed:
            return False
        pyautogui.hotkey('command', 'v')
        time.sleep(0.15)  # ensure paste completes and Command key fully releases
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, OSError):
        return False
    finally:
        # Restore the user's original clipboard, even on Ctrl+C mid-paste
        try:
            subprocess.run(['pbcopy'], input=saved_clipboard, check=False, timeout=2)
        except (subprocess.TimeoutExpired, OSError):
            pass


# Characters that mean "line break" in text copied from Word and others:
# vertical tab (Word soft break), form feed, NEL, Unicode line/para separators
LINE_BREAK_CHARS_RE = re.compile('[\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]')
# Other ASCII control characters: pyautogui has no key for them and drops them
CONTROL_CHARS_RE = re.compile('[\x00-\x08\x0e-\x1b\x1f\x7f]')


def normalize_newlines(text: str) -> str:
    """Make every line break a plain \\n and drop untypeable control chars.

    Windows line endings would otherwise type an extra Enter per line, and a
    Word soft break (\\x0b) would silently vanish, gluing two words together.
    """
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    text = LINE_BREAK_CHARS_RE.sub('\n', text)
    return CONTROL_CHARS_RE.sub('', text)


def clean_text(text: str, preserve_whitespace: bool = False) -> str:
    """Clean up the text: remove tabs, fix list spacing, handle separators.

    If preserve_whitespace is True, only normalizes smart quotes and trims
    trailing blank lines — indentation and alignment are kept intact.
    """
    text = normalize_newlines(text)

    # Normalize smart quotes/apostrophes to straight versions
    text = text.replace('\u2018', "'").replace('\u2019', "'")  # ' '
    text = text.replace('\u201C', '"').replace('\u201D', '"')  # " "

    if preserve_whitespace:
        # Convert tabs to spaces (4-space tab stops) to preserve alignment
        text = text.expandtabs(4)
        # Strip trailing blank lines only
        lines = text.split('\n')
        while lines and lines[-1].strip() == '':
            lines.pop()
        return '\n'.join(lines)

    # Replace bullet point characters with dashes. A bullet opening a line
    # becomes a proper "- " list marker ("•item" -> "- item").
    text = re.sub(r'^[ \t]*[•◦▪▸►▻●○■□▶‣⁃∙][ \t]*', '- ', text, flags=re.MULTILINE)
    text = re.sub(r'[•◦▪▸►▻●○■□▶‣⁃∙]', '-', text)
    # A line made only of dash/rule characters is a separator
    text = re.sub(r'^[ \t]*[⸻━─—–]+[ \t]*$', '---', text, flags=re.MULTILINE)
    # Replace em/en dashes used as bullets (at start of line) with regular dashes.
    # [ \t]*, not \s*: \s would eat the newline and fuse two lines.
    text = re.sub(r'^[ \t]*[—–][ \t]*(?=\S)', '- ', text, flags=re.MULTILINE)
    # Replace remaining em/en dashes with regular dashes
    text = text.replace('—', '-').replace('–', '-')

    # An interior tab separates words ("Introduction\t3"); keep a space
    text = re.sub(r'[ \t]*\t[ \t]*', ' ', text)

    lines = text.split('\n')
    cleaned_lines = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        is_separator = False
        if stripped:
            if len(stripped) >= 3 and all(c in '-_=~' for c in stripped):
                is_separator = True

        if is_separator:
            if cleaned_lines and cleaned_lines[-1] != SEPARATOR_MARKER:
                cleaned_lines.append(SEPARATOR_MARKER)
            i += 1
            continue

        if not stripped:
            # Preserve single blank lines as paragraph breaks, skip consecutive ones
            if cleaned_lines and cleaned_lines[-1] != '':
                cleaned_lines.append('')
            i += 1
            continue

        cleaned_lines.append(stripped)
        i += 1

    while cleaned_lines and cleaned_lines[-1] in (SEPARATOR_MARKER, ''):
        cleaned_lines.pop()

    text = '\n'.join(cleaned_lines)
    # "1.Item" -> "1. Item", but only at line start and never before a digit,
    # so "$4.99" and "v1.3.1" survive untouched.
    text = re.sub(r'^(\d+\.)(?=[^\s\d])', r'\1 ', text, flags=re.MULTILINE)
    # Collapse "-   item" to "- item". Requires existing whitespace so "-5",
    # "**bold**" and "-->" are left alone.
    text = re.sub(r'^([-*])[ \t]+(?=\S)', r'\1 ', text, flags=re.MULTILINE)

    return text.strip()


# Non-ASCII characters with a sensible keyboard equivalent, for ASCII-only mode
ASCII_REPLACEMENTS = {
    '…': '...',
    '—': '-', '–': '-', '‒': '-', '―': '-', '−': '-', '‐': '-', '‑': '-',
    '‘': "'", '’': "'", '‚': "'", '‛': "'", '′': "'",
    '“': '"', '”': '"', '„': '"', '‟': '"', '″': '"', '«': '"', '»': '"',
    '→': '->', '⟶': '->', '➜': '->', '➔': '->', '➝': '->', '➞': '->',
    '➟': '->', '➠': '->', '⇾': '->', '←': '<-', '⇒': '=>', '↔': '<->',
    '•': '-', '◦': '-', '▪': '-', '▸': '-', '►': '-', '▻': '-', '●': '-',
    '○': '-', '■': '-', '□': '-', '▶': '-', '‣': '-', '⁃': '-', '∙': '-',
    '·': '-',
    '×': 'x', '÷': '/', '⁄': '/', '≤': '<=', '≥': '>=', '≠': '!=', '±': '+/-',
    '©': '(c)', '®': '(R)', '™': '(TM)', '°': ' deg',
    '≈': '~', '∞': 'inf', '€': 'EUR', '£': 'GBP', '¥': 'JPY', '¢': 'c',
    'ø': 'o', 'Ø': 'O', 'ß': 'ss', 'æ': 'ae', 'Æ': 'AE', 'œ': 'oe', 'Œ': 'OE',
    'ł': 'l', 'Ł': 'L', 'đ': 'd', 'Đ': 'D', 'ð': 'd', 'Ð': 'D', 'þ': 'th',
    'Þ': 'Th', 'ı': 'i', '¿': '?', '¡': '!',
    '⸻': '---', '━': '-', '─': '-',
    ' ': ' ', ' ': ' ', ' ': ' ', ' ': ' ', ' ': ' ',
    ' ': ' ', ' ': ' ', ' ': ' ', ' ': ' ', ' ': ' ',
    ' ': ' ', '​': '', '‌': '', '‍': '', '⁠': '',
    '﻿': '',
}


def to_ascii(text: str) -> tuple:
    """Reduce text to pure ASCII so every character is a real keystroke.

    Used by ASCII-only mode, where the clipboard-paste path must never run —
    e.g. inside a Windows VM, where the Mac clipboard and Cmd+V don't reach
    the guest. Known symbols get keyboard equivalents, accents are stripped
    (é -> e), and anything left over becomes '?'.

    Returns (ascii_text, number_of_characters_replaced_with_?).
    """
    text = re.sub('°(?=[CFK]\\b)', '', text)  # 25°C -> 25C, not "25 degC"
    text = ''.join(ASCII_REPLACEMENTS.get(c, c) for c in text)
    out = []
    lost = 0
    for c in unicodedata.normalize('NFKD', text):
        if c.isascii():
            out.append(c)
        elif unicodedata.category(c) == 'Mn':
            continue  # combining accent left over from NFKD
        else:
            mapped = ASCII_REPLACEMENTS.get(c)
            if mapped is not None:
                out.append(mapped)
            else:
                out.append('?')
                lost += 1
    return ''.join(out), lost


def count_non_ascii(text: str) -> int:
    """Number of characters type_string() would have to paste via clipboard."""
    return sum(1 for c in text if not c.isascii())


def countdown(seconds: int):
    """Display a visual countdown before typing starts."""
    print()
    print(f"{Colors.YELLOW}{Colors.BOLD}Get ready! Typing starts in...{Colors.RESET}")
    for i in range(seconds, 0, -1):
        print(f"  {Colors.CYAN}{Colors.BOLD}{i}{Colors.RESET}{Colors.GRAY}...{Colors.RESET}")
        time.sleep(1)
    print(f"  {Colors.GREEN}{Colors.BOLD}GO!{Colors.RESET}")
    print()


def type_newline(app_mode: str):
    """Type a newline appropriate for the application mode."""
    if app_mode == "excel":
        pyautogui.hotkey('alt', 'enter')
    else:
        pyautogui.press('enter')


# Markdown's |---|:---:| row. Outer pipes are optional ("--- | ---").
ALIGN_ROW_RE = re.compile(r'^\s*\|?\s*:?-+:?\s*(\|\s*:?-+:?\s*)*\|?\s*$')
PIPE_SPLIT_RE = re.compile(r'(?<!\\)\|')


def _pipe_cells(line: str) -> list:
    """Cells of a markdown table row, outer pipes optional, \\| kept literal."""
    s = line.strip()
    if s.startswith('|'):
        s = s[1:]
    if s.endswith('|') and not s.endswith('\\|'):
        s = s[:-1]
    return [c.strip().replace('\\|', '|') for c in PIPE_SPLIT_RE.split(s)]


def _pipe_table_lines(lines: list) -> list:
    """Lines that belong to a markdown pipe table.

    With an alignment row present, any line containing a pipe counts, so
    tables written without outer pipes work. Without one, a line must start
    with | and have at least two cells: "| quoted text" is not a table.
    """
    has_align = any('|' in l and ALIGN_ROW_RE.match(l) for l in lines)
    out = []
    for l in lines:
        s = l.strip()
        if not PIPE_SPLIT_RE.search(s):
            continue
        if has_align or (s.startswith('|') and len(_pipe_cells(s)) >= 2):
            out.append(l)
    return out


def _trim_blank_rows(rows: list) -> list:
    """Drop all-empty rows at the start and end; interior ones keep their slot."""
    while rows and not any(rows[0]):
        rows.pop(0)
    while rows and not any(rows[-1]):
        rows.pop()
    return rows


def _parse_tsv(text: str) -> list:
    """Tab-separated rows, honouring Excel's quoting for multi-line cells.

    Excel copies a cell containing a line break or quote as "line1\nline2"
    with inner quotes doubled. Such line breaks come back as <br>, which
    type_table turns into Alt+Enter. Hand-typed text with a stray quote
    falls back to a plain split rather than swallowing the rest of the paste.
    """
    naive = [[c.strip() for c in line.split('\t')] for line in text.split('\n')]
    if '"' not in text:
        return _trim_blank_rows(naive)
    try:
        quoted = list(csv.reader(io.StringIO(text), delimiter='\t', strict=True))
    except csv.Error:
        return _trim_blank_rows(naive)
    # An unbalanced quote makes csv swallow later tabs/lines into one cell
    if any('\t' in cell for row in quoted for cell in row):
        return _trim_blank_rows(naive)
    rows = [[cell.strip().replace('\n', '<br>') for cell in row] or [''] for row in quoted]
    return _trim_blank_rows(rows)


def parse_table(text: str) -> list:
    """Parse a table into a list of rows, each a list of cell strings.

    Auto-detects the delimiter:
      1. Pipe `|` markdown table (see _pipe_table_lines), unless more
         lines contain tabs than look like pipe rows
      2. Tab `\\t` (Excel/Word/HTML paste)
      3. Two or more consecutive spaces (text dump fallback)

    The markdown alignment row (e.g. `|---|:---:|`) right after the header is
    filtered out. Empty rows inside the table keep their slot so the rows
    below land where they should; `\\|` is a literal pipe inside a cell.
    """
    text = normalize_newlines(text)
    lines = text.split('\n')

    pipe_lines = _pipe_table_lines(lines)
    tab_lines = [l for l in lines if '\t' in l]

    # Strategy 1: pipe-delimited markdown
    if pipe_lines and len(pipe_lines) >= len(tab_lines):
        pipe_rows = []
        skipped_align = False
        for line in pipe_lines:
            if (len(pipe_rows) == 1 and not skipped_align
                    and ALIGN_ROW_RE.match(line)):
                skipped_align = True
                continue  # the |---|---| row under the header
            pipe_rows.append(_pipe_cells(line))
        return _trim_blank_rows(pipe_rows)

    # Strategy 2: tab-delimited
    if tab_lines:
        return _parse_tsv(text)

    # Strategy 3: 2+ consecutive spaces
    space_re = re.compile(r' {2,}')
    space_rows = []
    for line in lines:
        s = line.strip()
        if not s or not space_re.search(s):
            continue
        cells = [c.strip() for c in space_re.split(s) if c.strip()]
        if cells:
            space_rows.append(cells)
    if space_rows:
        return space_rows

    return []


def is_grid_paste(text: str) -> bool:
    """True if the text is unambiguously a multi-row table.

    Deliberately stricter than parse_table(): only real tabs or markdown pipes
    count, and 2+ rows are required. This gates the Excel-mode auto-route,
    where a false positive would silently type into the wrong cells.
    """
    lines = [l for l in normalize_newlines(text).split('\n') if l.strip()]
    tabbed = sum(1 for l in lines if '\t' in l)
    piped = len(_pipe_table_lines(lines))
    return tabbed >= 2 or piped >= 2


# Arrows used as range separators (e.g. "21-Sep → 12-Oct")
ARROW_RE = re.compile(r'\s*[→⟶⇒➜➔➝➞➟➠⇾]\s*')

# What counts as a start/end range separator for column splitting: an arrow,
# or a *spaced* en/em dash. The spaces matter — without them "26-Oct-26" would
# look like a range and get torn in half.
RANGE_SEP_RE = re.compile(r'\s*[→⟶⇒➜➔➝➞➟➠⇾]\s*|\s+[–—-]\s+')

# A range endpoint must look like a date: a month name, or digits split by
# / . - (21/9, 2026-10-12). Keeps "Pending → Done" and "5 - 3" in one cell.
DATE_LIKE_RE = re.compile(
    r'\b(jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b'
    r'|\d{1,4}[/.-]\d{1,2}',
    re.IGNORECASE)


def split_range(cell: str):
    """[start, end] if cell is a range like "21-Sep → 12-Oct", else None.

    Both sides must look like dates: "→ done" is an arrow bullet and
    "Pending → Done" a status change, not ranges.
    """
    parts = RANGE_SEP_RE.split(cell, maxsplit=1)
    if len(parts) == 2 and all(DATE_LIKE_RE.search(p) for p in parts):
        return [parts[0].strip(), parts[1].strip()]
    return None


def split_range_columns(rows: list) -> list:
    """Expand every column containing a date range into a start/end pair.

    A column is split if *any* row has a range in it, so the result stays
    rectangular: range cells become [start, end], and every other cell in
    that column becomes [value, ''] — the blank reserving the end-date slot.
    Columns with no ranges anywhere (labels like "Task Owner") are untouched.

    Returns rows unchanged when the table contains no ranges at all.
    """
    if not rows:
        return rows

    width = max(len(r) for r in rows)
    split_cols = {
        col for col in range(width)
        if any(split_range(r[col]) for r in rows if col < len(r))
    }
    if not split_cols:
        return rows

    expanded = []
    for row in rows:
        out = []
        for col in range(len(row)):
            cell = row[col]
            if col not in split_cols:
                out.append(cell)
                continue
            parts = split_range(cell)
            if parts:
                out.extend(parts)
            else:
                # Single value (or blank) — occupies start, end left empty
                out.extend([cell, ''])
        expanded.append(out)
    return expanded


def normalize_cell(cell: str) -> str:
    """Reduce a table cell to pure ASCII wherever there's a sane equivalent.

    Arrows become " - ", em/en dashes and bullets become "-", smart quotes
    become straight quotes. This keeps cells typeable as plain keystrokes so
    type_string() never falls back to the clipboard-paste path, which is slow
    and briefly takes over the user's clipboard. Anything without an ASCII
    equivalent is left alone and still pastes correctly.
    """
    cell = cell.replace('‘', "'").replace('’', "'")
    cell = cell.replace('“', '"').replace('”', '"')
    cell = ARROW_RE.sub(' - ', cell)
    cell = re.sub(r'[—–]', '-', cell)
    cell = re.sub(r'[•◦▪▸►▻●○■□▶‣⁃∙]', '-', cell)
    return re.sub(r'[ \t]+', ' ', cell).strip()


# A plain number Excel should keep as a number: -5, +3.2, 1,000, 12%
NUMERIC_RE = re.compile(r'[-+]?(\d[\d,]*)?\.?\d+([eE][-+]?\d+)?%?')


def excel_safe(cell: str) -> str:
    """Stop Excel from reading a text cell as a formula.

    Excel treats input starting with -, + or @ as a formula, so "- item" or
    "+1 555 0100" pops a "problem with this formula" dialog that swallows
    every keystroke after it. A leading apostrophe forces text and isn't
    displayed. Plain numbers ("-5") pass through, and "=" is left alone so
    typing a real formula still works.
    """
    if cell and cell[0] in '-+@' and not NUMERIC_RE.fullmatch(cell):
        return "'" + cell
    return cell


BR_RE = re.compile(r'<br\s*/?>', re.IGNORECASE)


def table_cells(text: str, ascii_only: bool = False) -> list:
    """Rows of cells exactly as type_table() will type them."""
    rows = split_range_columns(parse_table(text))
    out = []
    for row in rows:
        cells = []
        for cell in row:
            cell = normalize_cell(cell)
            if ascii_only:
                cell = to_ascii(cell)[0]
            cells.append(excel_safe(cell))
        out.append(cells)
    return out


def type_table(text: str, ascii_only: bool = False):
    """Type a table cell-by-cell into Excel.

    Position the cursor in the desired top-left cell before the countdown
    ends. Between cells: Tab. After the last cell of each row: Enter — Excel
    returns the cursor to the column where the Tab sequence started, so each
    new row begins under the original starting column. `<br>` inside a cell
    becomes Alt+Enter (in-cell line break). Cells are ASCII-normalized first
    (see normalize_cell) so typing stays pure keystrokes, and date ranges are
    split into start/end column pairs (see split_range_columns).
    """
    rows = table_cells(text, ascii_only)
    if not rows:
        return

    time.sleep(0.3)

    for row in rows:
        for cell_idx, cell in enumerate(row):
            parts = BR_RE.split(cell)
            for part_idx, part in enumerate(parts):
                if part:
                    type_string(part)
                if part_idx < len(parts) - 1:
                    pyautogui.hotkey('alt', 'enter')
                    time.sleep(0.05)

            if any(parts):
                # Excel AutoComplete may have appended a selected suggestion
                # ("A" -> "Apple" from the cell above). Forward-delete drops
                # it; with no suggestion showing it does nothing.
                pyautogui.press('delete')

            if cell_idx < len(row) - 1:
                pyautogui.press('tab')
            else:
                pyautogui.press('enter')
            time.sleep(calculate_delay())


def resolve_mode(text: str, app_mode: str) -> str:
    """Pick the mode actually used for this paste.

    Excel (single cell) mode given a real grid is almost always a mis-pick —
    it would cram the whole table into one cell via Alt+Enter. Route it to
    table mode instead and say so, rather than silently doing the wrong thing.
    """
    if app_mode == "excel" and is_grid_paste(text) and parse_table(text):
        print()
        print_info(
            f"Detected a table — switching to {Colors.CYAN}Excel Table/Grid{Colors.RESET} "
            f"for this paste {Colors.GRAY}(use [E] with plain text for single-cell){Colors.RESET}"
        )
        return "table"
    return app_mode


def prepare_text(text: str, app_mode: str, ascii_only: bool = False) -> str:
    """Clean text for a non-table mode exactly as type_text() will type it.

    Separators stay as SEPARATOR_MARKER lines (see preview_text). Compress
    mode comes back already joined onto one line.
    """
    preserve_ws = app_mode in ("sql", "text")
    # Clean first, then ASCII-ize: clean_text needs to see the original
    # bullets and rule characters (⸻, •) to turn them into separators/lists
    text = clean_text(text, preserve_whitespace=preserve_ws)
    if ascii_only:
        text = to_ascii(text)[0]
    if app_mode == "compress":
        lines = [line for line in text.split('\n') if line not in (SEPARATOR_MARKER, '')]
        return ' '.join(lines)
    if app_mode == "excel":
        text = excel_safe(text)
    return text


def type_text(text: str, app_mode: str, ascii_only: bool = False):
    """Type the given text with human-like delays.

    ascii_only reduces the text to pure ASCII first (see to_ascii) so nothing
    goes through the clipboard-paste path.
    """
    if app_mode == "table":
        type_table(text, ascii_only)
        return

    text = prepare_text(text, app_mode, ascii_only)

    if app_mode == "compress":
        time.sleep(0.3)
        type_string(text)
        return

    if app_mode == "sql":
        # SQL/Code mode: preserve formatting with auto-indent clearing.
        # After Enter, the target app may auto-indent unpredictably.
        # Instead of guessing, we clear any auto-indent with Home+Shift+End+Delete
        # then type the exact indentation fresh each line.
        lines = text.split('\n')
        time.sleep(0.3)

        for line_idx, line in enumerate(lines):
            # After any Enter (not the first line), clear auto-indent
            if line_idx > 0:
                pyautogui.press('home')
                time.sleep(0.05)
                pyautogui.hotkey('shift', 'end')
                time.sleep(0.05)
                pyautogui.press('delete')
                time.sleep(0.05)

            if line.strip() == '':
                pyautogui.press('enter')
                time.sleep(calculate_delay())
                continue

            target_indent = len(line) - len(line.lstrip(' '))
            rest = line[target_indent:]

            # Type the exact leading spaces
            for _ in range(target_indent):
                pyautogui.write(' ', interval=0)
                time.sleep(calculate_delay(is_word_boundary=True))

            # Type the rest of the line normally
            type_string(rest)

            if line_idx < len(lines) - 1:
                time.sleep(calculate_delay())
                pyautogui.press('enter')
                time.sleep(calculate_delay())
        return

    if app_mode == "text":
        # Plain Text mode: type everything exactly as-is.
        # No separator conversion, no bullet handling, just raw text with Enter.
        lines = text.split('\n')
        time.sleep(0.3)

        for line_idx, line in enumerate(lines):
            if line == '':
                pyautogui.press('enter')
                time.sleep(calculate_delay())
                continue

            type_string(line)

            if line_idx < len(lines) - 1:
                time.sleep(calculate_delay())
                pyautogui.press('enter')
                time.sleep(calculate_delay())
        return

    lines = text.split('\n')
    time.sleep(0.3)

    in_dash_list = False

    for line_idx, line in enumerate(lines):
        if line == SEPARATOR_MARKER:
            if in_dash_list and app_mode == "word":
                # End Word's auto-list first, or "---" lands on a bullet
                type_newline(app_mode)
            in_dash_list = False
            # Type the separator as visible text (---) instead of just a blank line
            type_string('---')
            if line_idx < len(lines) - 1:
                time.sleep(calculate_delay())
                type_newline(app_mode)
                time.sleep(calculate_delay())
            continue

        if line == '':
            # Paragraph break — extra Enter for visual spacing
            if in_dash_list and app_mode == "word":
                # End Word's auto-list by pressing Enter once more
                type_newline(app_mode)
            in_dash_list = False
            type_newline(app_mode)
            time.sleep(calculate_delay())
            continue

        is_dash_item = line.startswith('- ')

        if app_mode == "word" and is_dash_item and in_dash_list:
            # Word auto-continues the dash list, skip the leading "- "
            line = line[2:]

        if is_dash_item:
            in_dash_list = True
        else:
            if in_dash_list and app_mode == "word":
                # Leaving a dash list — press Enter to end Word's auto-list
                type_newline(app_mode)
            in_dash_list = False

        type_string(line)

        if line_idx < len(lines) - 1:
            time.sleep(calculate_delay())
            type_newline(app_mode)
            time.sleep(calculate_delay())

    if app_mode == "excel":
        # Drop any AutoComplete suggestion before the user commits the cell
        # (same as type_table)
        pyautogui.press('delete')


# ═══════════════════════════════════════════════════════════════════════════════
# USER INPUT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def stdin_has_pending(timeout: float = 0.1) -> bool:
    """True if more input is already waiting, i.e. a paste is still arriving.

    A terminal delivers a paste one line per read, so after a blank line the
    rest of a paste is still queued. A human pressing Enter never is.
    """
    if not sys.stdin.isatty():
        return False
    import select as sel
    try:
        return bool(sel.select([sys.stdin], [], [], timeout)[0])
    except (OSError, ValueError):
        return False


# macOS terminals silently cut a single pasted line at 1024 bytes
TTY_LINE_LIMIT = 1024


def get_multiline_input(first_line: str = None):
    """Collect multiline text input until two consecutive empty lines.

    Blank lines that arrive mid-paste don't count toward the two, so a pasted
    document with double blank lines comes through whole. Returns None when
    stdin is closed and nothing was entered.
    """
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}Paste or type your text below{Colors.RESET}")
    print(f"{Colors.GRAY}   Press Enter 3 times when done{Colors.RESET}")
    print()

    lines = []

    if first_line:
        preview = first_line[:50] + ('...' if len(first_line) > 50 else '')
        print(f"   {Colors.DIM}Captured: {preview}{Colors.RESET}")
        lines.append(first_line)

    empty_count = 0
    got_eof = False
    while True:
        try:
            line = input()
        except EOFError:
            got_eof = True
            break
        if line == "":
            empty_count += 1
            if empty_count >= 2 and not stdin_has_pending():
                break
            lines.append(line)  # preserve blank lines (paragraph breaks)
        else:
            empty_count = 0
            lines.append(line)

    while lines and lines[-1] == '':
        lines.pop()

    if got_eof and not lines:
        return None

    if any(len(l.encode('utf-8')) >= TTY_LINE_LIMIT - 1 for l in lines):
        print_warning(
            f"A line is over {TTY_LINE_LIMIT} bytes — the terminal may have cut it short. "
            f"To be safe, pass the file instead: python lazy_typer.py <file>"
        )

    return '\n'.join(lines)


def get_app_mode() -> str:
    """Prompt user to select application mode."""
    while True:
        print()
        print(f"{Colors.CYAN}{Colors.BOLD}📋 Select Application Mode{Colors.RESET}")
        print_divider()
        print(f"  {Colors.YELLOW}[W]{Colors.RESET}  {Colors.WHITE}Microsoft Word{Colors.RESET}")
        print(f"       {Colors.GRAY}Enter for line breaks{Colors.RESET}")
        print()
        print(f"  {Colors.YELLOW}[E]{Colors.RESET}  {Colors.WHITE}Excel - Single Cell{Colors.RESET}")
        print(f"       {Colors.GRAY}All text into ONE cell, Alt+Enter line breaks{Colors.RESET}")
        print()
        print(f"  {Colors.YELLOW}[B]{Colors.RESET}  {Colors.WHITE}Excel - Table / Grid{Colors.RESET}")
        print(f"       {Colors.GRAY}Fills MANY cells: Tab between, Enter per row{Colors.RESET}")
        print()
        print(f"  {Colors.YELLOW}[T]{Colors.RESET}  {Colors.WHITE}Plain Text{Colors.RESET}")
        print(f"       {Colors.GRAY}Exact copy - preserves all formatting{Colors.RESET}")
        print()
        print(f"  {Colors.YELLOW}[S]{Colors.RESET}  {Colors.WHITE}SQL / Code Mode{Colors.RESET}")
        print(f"       {Colors.GRAY}Preserves indentation, clears auto-indent{Colors.RESET}")
        print()
        print(f"  {Colors.YELLOW}[C]{Colors.RESET}  {Colors.WHITE}Compress Mode{Colors.RESET}")
        print(f"       {Colors.GRAY}All text on one line, no line breaks{Colors.RESET}")
        print_divider()
        print(f"  {Colors.GRAY}Press Ctrl+C to quit{Colors.RESET}")

        choice = input(f"\n{Colors.CYAN}Enter choice (W/E/B/T/S/C):{Colors.RESET} ").strip().lower()

        if choice in ('w', 'word'):
            print_success("Mode set: Microsoft Word")
            return "word"
        elif choice in ('e', 'excel'):
            print_success("Mode set: Excel - Single Cell")
            return "excel"
        elif choice in ('b', 'table'):
            print_success("Mode set: Excel - Table / Grid")
            return "table"
        elif choice in ('t', 'text'):
            print_success("Mode set: Plain Text (exact copy)")
            return "text"
        elif choice in ('s', 'sql'):
            print_success("Mode set: SQL / Code (preserves formatting)")
            return "sql"
        elif choice in ('c', 'compress'):
            print_success("Mode set: Compress (single line)")
            return "compress"
        else:
            print_error("Invalid choice. Please enter W, E, B, T, S, or C.")


def format_duration(seconds: float) -> str:
    """'42.0 seconds' under two minutes, '6 min 14 s' above."""
    if seconds < 120:
        return f"{seconds:.1f} seconds"
    minutes, secs = divmod(int(round(seconds)), 60)
    return f"{minutes} min {secs} s"


def show_ready_message(char_count: int, word_count: int, estimated_time: float,
                       pasted_chars: int = 0, lost_chars: int = 0):
    """Show the ready message before typing.

    pasted_chars: non-ASCII characters that will go through the clipboard.
    lost_chars: characters ASCII-only mode had to replace with '?'.
    """
    print()
    print_divider()
    print(f"  {Colors.WHITE}{Colors.BOLD}📊 Ready to type:{Colors.RESET}")
    print(f"     {Colors.CYAN}{char_count}{Colors.RESET} characters  •  {Colors.CYAN}~{word_count}{Colors.RESET} words")
    print(f"     {Colors.GRAY}Estimated time: ~{format_duration(estimated_time)}{Colors.RESET}")
    if pasted_chars:
        print(f"     {Colors.YELLOW}{pasted_chars} special character(s) will be pasted via the clipboard{Colors.RESET}")
        print(f"     {Colors.GRAY}In a VM? Press [A] at the menu for ASCII-only typing{Colors.RESET}")
    if lost_chars:
        print(f"     {Colors.YELLOW}ASCII-only: {lost_chars} character(s) have no ASCII form and will type as '?'{Colors.RESET}")
    print_divider()
    print()
    print(f"  {Colors.YELLOW}{Colors.BOLD}👉 Switch to your target application now!{Colors.RESET}")


def show_done_message(app_mode: str):
    """Show the completion message with current mode."""
    mode_name = MODE_DISPLAY.get(app_mode, app_mode)
    print()
    print(f"{Colors.GREEN}{Colors.BOLD}╔═══════════════════════════════════════════════════════╗{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}║          Done! Text has been typed.                   ║{Colors.RESET}")
    print(f"{Colors.GREEN}{Colors.BOLD}╚═══════════════════════════════════════════════════════╝{Colors.RESET}")
    print(f"  {Colors.GRAY}Mode: {Colors.CYAN}{mode_name}{Colors.RESET}")


def get_countdown() -> int:
    """Prompt user to set countdown seconds."""
    while True:
        print()
        print(f"{Colors.CYAN}{Colors.BOLD}Set Countdown Timer{Colors.RESET}")
        print_divider()
        print(f"  {Colors.GRAY}Enter a number between 1 and 10{Colors.RESET}")
        print(f"  {Colors.GRAY}Press Enter for default ({DEFAULT_COUNTDOWN}s){Colors.RESET}")
        print_divider()

        choice = input(f"\n{Colors.CYAN}Seconds:{Colors.RESET} ").strip()

        if choice == '':
            print_success(f"Countdown set: {DEFAULT_COUNTDOWN} seconds")
            return DEFAULT_COUNTDOWN

        try:
            seconds = int(choice)
            if 1 <= seconds <= 10:
                print_success(f"Countdown set: {seconds} seconds")
                return seconds
            else:
                print_error("Please enter a number between 1 and 10.")
        except ValueError:
            print_error("Invalid input. Please enter a number.")


def show_menu(countdown_seconds: int, app_mode: str, ascii_only: bool = False):
    """Show the options menu."""
    mode_name = MODE_DISPLAY.get(app_mode, app_mode)
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}What's next?{Colors.RESET}")
    print_divider()
    print(f"  {Colors.YELLOW}[Enter]{Colors.RESET}  Type more text")
    print(f"  {Colors.YELLOW}[W/E/B/T/S/C]{Colors.RESET}  Switch mode ({mode_name})")
    print(f"  {Colors.YELLOW}[#]{Colors.RESET}      Change countdown timer ({countdown_seconds}s)")
    print(f"  {Colors.YELLOW}[A]{Colors.RESET}      ASCII-only typing ({'on' if ascii_only else 'off'}) - no clipboard, for VMs")
    print(f"  {Colors.YELLOW}[Q]{Colors.RESET}      Quit")
    print(f"  {Colors.GRAY}Or just paste your next text directly!{Colors.RESET}")
    print_divider()


# ═══════════════════════════════════════════════════════════════════════════════
# VERSION CHECK
# ═══════════════════════════════════════════════════════════════════════════════

def check_for_latest_version():
    """Check GitHub for a newer release. Returns (version, url) or None.

    Uses curl instead of urllib to avoid macOS Python SSL certificate issues.
    Silently returns None on any network or parse error.
    """
    url = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "2", "--max-time", "5",
             "-H", "Accept: application/vnd.github+json",
             "-H", "User-Agent: lazy-typer-update-check",
             url],
            capture_output=True, text=True, timeout=7
        )
        if result.returncode != 0:
            return None

        data = json.loads(result.stdout)
        if data.get("prerelease") or data.get("draft"):
            return None
        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")
        html_url = data.get("html_url", "")

        # Strictly greater — a plain != would offer a "downgrade update" whenever
        # the local version is ahead of the published release (e.g. during dev),
        # and accepting that runs git reset --hard over your uncommitted work.
        if '-' in latest:
            return None  # "1.4.0-rc.1" is a prerelease, not a stable update
        if latest and version_tuple(latest) > version_tuple(VERSION):
            return (latest, html_url)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError,
            KeyError, OSError, ValueError, AttributeError, TypeError,
            RecursionError):
        # AttributeError/TypeError: the API answered with valid JSON that
        # isn't a release object (a list, or null)
        return None


def arrow_key_select(options, selected=0):
    """Interactive arrow-key menu. Returns selected index.

    Uses tty.setcbreak() for raw input on macOS/Linux.
    Falls back to numbered input if terminal is not a TTY.
    """
    import select as sel

    if not sys.stdin.isatty():
        for i, opt in enumerate(options):
            print(f"  [{i + 1}] {opt}")
        try:
            choice = input("Choice: ").strip()
        except EOFError:
            return len(options) - 1
        try:
            idx = int(choice) - 1
            return idx if 0 <= idx < len(options) else len(options) - 1
        except (ValueError, IndexError):
            return len(options) - 1

    import tty, termios

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    num_opts = len(options)

    def draw():
        sys.stdout.write(f"\033[{num_opts}A")
        for i, opt in enumerate(options):
            if i == selected:
                sys.stdout.write(
                    f"\r  {Colors.GREEN}{Colors.BOLD}> {opt}{Colors.RESET}\033[K\n"
                )
            else:
                sys.stdout.write(
                    f"\r    {Colors.GRAY}{opt}{Colors.RESET}\033[K\n"
                )
        sys.stdout.flush()

    for _ in options:
        print()
    draw()

    try:
        tty.setcbreak(fd)
        while True:
            b = os.read(fd, 1)

            if b == b'':
                # Terminal closed: pick the last (safe) option, don't spin
                selected = num_opts - 1
                break
            if b in (b'\r', b'\n'):
                break
            if b == b'\x03':
                raise KeyboardInterrupt

            if b == b'\x1b':
                if sel.select([fd], [], [], 0.05)[0]:
                    b2 = os.read(fd, 1)
                    # ESC [ A in normal mode, ESC O A in application cursor mode
                    if b2 in (b'[', b'O') and sel.select([fd], [], [], 0.05)[0]:
                        b3 = os.read(fd, 1)
                        if b3 == b'A':
                            selected = (selected - 1) % num_opts
                        elif b3 == b'B':
                            selected = (selected + 1) % num_opts
                        draw()
                else:
                    selected = num_opts - 1
                    break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    print()
    return selected


def version_tuple(v: str) -> tuple:
    """Parse a dotted version into a comparable tuple. Non-numeric parts sort last."""
    parts = []
    for part in v.split('.'):
        digits = re.match(r'\d+', part)
        parts.append(int(digits.group()) if digits else 0)
    # Drop trailing zeros so "1.3" and "1.3.0" compare equal
    while len(parts) > 1 and parts[-1] == 0:
        parts.pop()
    return tuple(parts)


def has_uncommitted_changes(script_dir: str) -> bool:
    """True if the repo has uncommitted work that an update would destroy."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=script_dir, capture_output=True, text=True, timeout=10
        )
        # A failing git status can't vouch for a clean tree — assume dirty
        return result.returncode != 0 or bool(result.stdout.strip())
    except (subprocess.TimeoutExpired, OSError):
        # Can't tell — assume dirty so we never silently discard work
        return True


def git(script_dir: str, *args, timeout: int = 10):
    """Run a git command that can never stop to ask for a password or host key.

    stdout/stderr are captured, so a prompt would be invisible and the
    update would just appear to hang.
    """
    env = dict(os.environ, GIT_TERMINAL_PROMPT='0',
               GIT_SSH_COMMAND='ssh -o BatchMode=yes')
    return subprocess.run(
        ["git", *args], cwd=script_dir, capture_output=True, text=True,
        timeout=timeout, stdin=subprocess.DEVNULL, env=env
    )


def is_lazy_typer_checkout(script_dir: str) -> bool:
    """True only if script_dir is the root of a clone whose origin is GITHUB_REPO.

    Without this, a lazy_typer.py copied into some other repo would make the
    updater hard-reset *that* repo to its origin/main.
    """
    try:
        top = git(script_dir, "rev-parse", "--show-toplevel")
        url = git(script_dir, "remote", "get-url", "origin")
    except (subprocess.TimeoutExpired, OSError):
        return False
    if top.returncode != 0 or url.returncode != 0:
        return False
    if os.path.realpath(top.stdout.strip()) != os.path.realpath(script_dir):
        return False
    slug = re.sub(r'\.git$', '', url.stdout.strip().rstrip('/')).lower()
    return slug.endswith('/' + GITHUB_REPO.lower()) or slug.endswith(':' + GITHUB_REPO.lower())


def run_git_pull():
    """Fetch and reset to origin/main. Returns True on success.

    Refuses to run when the working tree is dirty: `git reset --hard`
    permanently destroys uncommitted changes with no way to recover them.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))

    if not is_lazy_typer_checkout(script_dir):
        print_error("This folder isn't a git clone of lazy-typer — update cancelled.")
        print_info(f"Download the new version from https://github.com/{GITHUB_REPO}")
        return False

    if has_uncommitted_changes(script_dir):
        print_error("You have uncommitted changes — update cancelled.")
        print_warning("Updating runs 'git reset --hard', which would delete them permanently.")
        print_info("Commit or stash your work first, then update:")
        print(f"    {Colors.GRAY}git stash        {Colors.RESET}{Colors.DIM}# or: git commit -am 'wip'{Colors.RESET}")
        return False

    try:
        fetch = git(script_dir, "fetch", "origin", timeout=30)
        if fetch.returncode != 0:
            print_error(f"Update failed: {fetch.stderr.strip()}")
            return False

        # reset --hard would also orphan local commits and move whatever
        # branch is checked out onto main. Only update a plain main checkout.
        branch = git(script_dir, "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        if branch != "main":
            print_error(f"You're on branch '{branch or 'unknown'}', not main — update cancelled.")
            return False
        ahead = git(script_dir, "rev-list", "--count", "origin/main..HEAD")
        if ahead.returncode != 0 or ahead.stdout.strip() != "0":
            print_error("You have local commits that aren't on GitHub — update cancelled.")
            print_warning("Updating runs 'git reset --hard', which would drop them.")
            print_info("Push them first, then update.")
            return False

        reset = git(script_dir, "reset", "--hard", "origin/main")
        if reset.returncode == 0:
            print_success("Updated successfully!")
            return True
        else:
            print_error(f"Update failed: {reset.stderr.strip()}")
            return False
    except subprocess.TimeoutExpired:
        print_error("Update timed out. Check your network connection.")
        return False
    except FileNotFoundError:
        print_error("git not found. Please install git or update manually.")
        return False
    except OSError as e:
        print_error(f"Update failed: {e}")
        return False


def check_and_prompt_update():
    """Check for updates and prompt user if a new version is available."""
    update_info = check_for_latest_version()
    if update_info is None:
        return

    latest, url = update_info

    if not sys.stdin.isatty():
        # Piped input is the text to type, not an answer to this prompt
        print_info(f"New version available: v{latest} (run interactively to update)")
        return

    print()
    print(f"  {Colors.YELLOW}{Colors.BOLD}New version available: v{latest}{Colors.RESET}"
          f"  {Colors.GRAY}(current: v{VERSION}){Colors.RESET}")
    print()

    choice = arrow_key_select(["Update Now", "Continue"], selected=0)

    if choice == 0:
        print()
        if run_git_pull():
            print()
            print_info("Restarting with updated version...")
            time.sleep(1)
            # Clear bytecode cache so Python re-reads the updated source
            cache_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '__pycache__')
            if os.path.isdir(cache_dir):
                shutil.rmtree(cache_dir)
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            print()
            print_warning("Continuing with current version.")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

def preview_text(text: str, app_mode: str, ascii_only: bool = False) -> tuple:
    """(text as it will be typed, chars ASCII-only mode turns into '?').

    Built from the same helpers type_text() uses, so counts and warnings
    match the keystrokes.
    """
    if app_mode == "table":
        lost = 0
        if ascii_only:
            lost = sum(to_ascii(normalize_cell(c))[1]
                       for row in split_range_columns(parse_table(text)) for c in row)
        rows = table_cells(text, ascii_only)
        typed = '\n'.join('\t'.join(BR_RE.sub('\n', c) for c in row) for row in rows)
        return typed, lost
    typed = prepare_text(text, app_mode).replace(SEPARATOR_MARKER, '---')
    if not ascii_only:
        return typed, 0
    return to_ascii(typed)


def run_typing_pass(text: str, app_mode: str, countdown_seconds: int,
                    ascii_only: bool = False) -> bool:
    """Validate, preview, count down and type one paste. False if nothing typed."""
    effective_mode = resolve_mode(text, app_mode)

    if effective_mode == "table" and not parse_table(text):
        print_warning("No table rows detected. Use markdown |, tabs, or 2+ spaces between columns.")
        return False

    preview, lost = preview_text(text, effective_mode, ascii_only)
    if not preview.strip():
        print_warning("Nothing to type after cleanup (only separators or blank lines).")
        return False
    char_count = len(preview)
    word_count = len(preview.split())
    pasted = count_non_ascii(preview)

    show_ready_message(char_count, word_count, char_count * BASE_DELAY, pasted, lost)
    countdown(countdown_seconds)
    type_text(text, effective_mode, ascii_only)
    flush_stdin()
    show_done_message(effective_mode)
    return True


def flush_stdin():
    """Discard anything typed into the terminal while we were typing.

    If focus slips back to the terminal mid-run, our own keystrokes land in
    stdin and would otherwise be read as the next menu choice or paste.
    """
    if not sys.stdin.isatty():
        return
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)
    except (ImportError, OSError, ValueError):
        pass


MODE_KEYS = {
    'w': "word", 'word': "word",
    'e': "excel", 'excel': "excel",
    'b': "table", 'table': "table",
    't': "text", 'text': "text",
    's': "sql", 'sql': "sql",
    'c': "compress", 'compress': "compress",
}

MODE_SET_MESSAGES = {
    "word": "Mode set: Microsoft Word",
    "excel": "Mode set: Excel - Single Cell",
    "table": "Mode set: Excel - Table / Grid",
    "text": "Mode set: Plain Text (exact copy)",
    "sql": "Mode set: SQL / Code (preserves formatting)",
    "compress": "Mode set: Compress (single line)",
}


def read_text_file(path: str) -> str:
    """Read a file to type. Exits with a message if it can't be read."""
    path = os.path.expanduser(path)
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        if raw.startswith((b'\xff\xfe', b'\xfe\xff')):
            text = raw.decode('utf-16')  # Notepad/Word "Unicode" save
        else:
            text = raw.decode('utf-8-sig')
    except FileNotFoundError:
        print_error(f"File not found: {path}")
        sys.exit(1)
    except IsADirectoryError:
        print_error(f"That's a folder, not a file: {path}")
        sys.exit(1)
    except UnicodeDecodeError:
        print_error(f"Not a UTF-8 text file: {path}")
        sys.exit(1)
    except OSError as e:
        print_error(f"Can't read {path}: {e}")
        sys.exit(1)
    text = text.replace('\r\n', '\n').replace('\r', '\n')
    if not text.strip():
        print_error(f"File is empty: {path}")
        sys.exit(1)
    return text


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Type text into any app like a human at ~250 WPM.")
    parser.add_argument(
        "file", nargs="?",
        help="type this file's contents instead of pasting text")
    parser.add_argument(
        "--mode", choices=sorted(set(MODE_KEYS.values())),
        help="skip the mode prompt (text = exact copy)")
    parser.add_argument(
        "--ascii", action="store_true",
        help="ASCII-only: type ... and - instead of pasting special characters "
             "through the clipboard (use inside a VM)")
    return parser.parse_args(argv)


def main(argv=None):
    """Main loop for the Lazy Typer."""
    args = parse_args(argv)
    # Read the file before anything else so a bad path fails fast
    pending_text = read_text_file(args.file) if args.file else None
    ascii_only = args.ascii

    check_and_prompt_update()
    print_header()
    if args.mode:
        app_mode = args.mode
        print_success(MODE_SET_MESSAGES[app_mode])
    else:
        app_mode = get_app_mode()
    if ascii_only:
        print_success("ASCII-only typing: on")
    countdown_seconds = get_countdown()

    if pending_text is not None:
        print_info(f"Loaded {args.file}")

    while True:
        from_paste = pending_text is None
        if from_paste:
            text = get_multiline_input()
            if text is None:
                print()
                print_info("Input closed. Goodbye! 👋")
                sys.exit(0)
        else:
            text, pending_text = pending_text, None

        # Only a typed "quit" quits; a file that says "quit" gets typed
        if from_paste and text.strip().lower() == 'quit':
            print()
            print_info("Goodbye! 👋")
            sys.exit(0)

        if not text.strip():
            print_warning("No text entered. Try again or type 'quit' to exit.")
            continue

        if not run_typing_pass(text, app_mode, countdown_seconds, ascii_only):
            continue

        show_menu(countdown_seconds, app_mode, ascii_only)
        try:
            raw = input(f"\n{Colors.CYAN}Your choice:{Colors.RESET} ")
        except EOFError:
            print()
            print_info("Input closed. Goodbye! 👋")
            sys.exit(0)
        choice = raw.strip().lower()

        if choice and stdin_has_pending():
            # More lines are already queued: this is a paste whose first line
            # happens to look like a command ("Text", "2024", "Q")
            pending_text = get_multiline_input(first_line=raw)
            if pending_text is None:
                print()
                print_info("Input closed. Goodbye! 👋")
                sys.exit(0)
            continue

        if choice == 'q':
            print()
            print_info("Goodbye! 👋")
            sys.exit(0)
        elif choice in MODE_KEYS:
            app_mode = MODE_KEYS[choice]
            print_success(MODE_SET_MESSAGES[app_mode])
        elif choice == 'm':
            app_mode = get_app_mode()
        elif choice == 'a':
            ascii_only = not ascii_only
            print_success(f"ASCII-only typing: {'on' if ascii_only else 'off'}")
        elif re.fullmatch(r'[0-9]{1,3}', choice) and 1 <= int(choice) <= 10:
            countdown_seconds = int(choice)
            print_success(f"Countdown set: {countdown_seconds} seconds")
        elif re.fullmatch(r'[0-9]{1,3}', choice):
            countdown_seconds = get_countdown()
        elif raw == '':
            pass
        else:
            # Anything else, including an indentation-only line, starts a paste
            # Pasted text straight at the menu: keep the raw first line so
            # its indentation survives (matters for SQL / Plain Text)
            pending_text = get_multiline_input(first_line=raw)
            if pending_text is None:
                print()
                print_info("Input closed. Goodbye! 👋")
                sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print()
        print()
        print_info("Interrupted. Goodbye! 👋")
        sys.exit(0)
