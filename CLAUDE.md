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
python lazy_typer.py FILE [--mode text] [--ascii]

# Tests (pyautogui and the clipboard are faked; nothing is really typed)
python3 -m pytest -q tests
```

**Never run the script for real while testing** — pyautogui sends real keystrokes to whatever app has focus. Use the `keyboard` fixture in `tests/conftest.py`.

## Architecture

Single-file application (`lazy_typer.py`) with these sections:

- **Colors class**: ANSI color codes for terminal output styling
- **Configuration constants**: WPM (250), VARIATION (0.45), DEFAULT_COUNTDOWN (5), VERSION, GITHUB_REPO
- **`clean_text()`**: Text preprocessor — normalizes smart quotes to straight quotes, converts Unicode bullets to dashes, removes tabs, converts separator lines, fixes list spacing, preserves paragraph breaks
- **`type_text()`**: Core typing loop using pyautogui with per-character delays and paragraph break handling
- **`type_newline()`**: Mode-aware newline handling (Enter for Word, Alt+Enter for Excel)
- **`get_multiline_input()`**: Multi-line text input with `empty_count` tracker — requires 2 consecutive empty lines to terminate, preserving paragraph breaks
- **Version check system**: `check_and_prompt_update()` → `check_for_latest_version()` → `arrow_key_select()` → `run_git_pull()`
- **`main()`**: Startup flow: version check → header → mode selection → countdown → typing loop

## Application Modes

- **Word**: Standard Enter key for newlines
- **Excel - Single Cell**: Alt+Enter for in-cell line breaks; everything lands in one cell
- **Excel - Table / Grid**: Tab between cells, Enter at row end (Excel returns to the starting column). Cells pass through `normalize_cell()` first
- **Plain Text**: Exact 1:1 copy, only smart quotes normalized
- **SQL / Code**: Preserves indentation, clears the editor's auto-indent per line
- **Compress**: All text on single line, no line breaks

## Table Mode Notes

- `parse_table()` auto-detects the delimiter: markdown `|` → tabs → 2+ spaces. Pipe rows need 2+ cells unless an alignment row is present (then outer pipes are optional); `\|` is a literal pipe; tabs win if more lines have tabs than pipes
- Interior blank rows keep their slot (only leading/trailing ones are trimmed) — dropping one shifts every later row up into the wrong cells. Same for single-cell rows in a TSV paste
- Tab pastes containing `"` go through `csv` so Excel's quoted multi-line cells parse; a cell that ends up containing a tab means an unbalanced quote, and parsing falls back to a plain split
- `table_cells()` is the single source of what gets typed per cell; `type_table()` and `preview_text()` both use it so the ready-message counts match
- `is_grid_paste()` is deliberately stricter than `parse_table()` — tabs or pipes only, 2+ rows. It gates the Excel-mode auto-route, where a false positive would silently type into the wrong cells
- `resolve_mode()` routes Excel mode to table mode for grid pastes and prints a notice. Never make this silent
- `normalize_cell()` ASCII-izes cells so `type_string()` avoids its clipboard-paste path, which is slow and briefly hijacks the user's clipboard
- `split_range_columns()` expands any column containing a date range into a start/end pair. It is column-wise on purpose: splitting only the range *cells* would leave range rows wider than single-date rows and shear the grid. Single values get `[value, '']`
- `RANGE_SEP_RE` requires *spaces* around dashes (en, em or ASCII). Without that, `26-Oct-26` parses as a range and gets torn in half — there is a regression test for exactly this
- `split_range()` also requires both endpoints to match `DATE_LIKE_RE`, so `Pending → Done` and `→ done` don't add a column
- A table with no ranges passes through `split_range_columns()` unchanged, so the feature is inert for non-date tables
- `excel_safe()` prefixes `'` to text starting with `-`, `+` or `@` (Excel would open a formula-error dialog that eats every later keystroke). Plain numbers and `=` formulas pass through
- `type_table()` presses Forward Delete after each non-empty cell to drop Excel AutoComplete suggestions
- Merged cells in the target sheet break the Tab/Enter alignment — an Excel constraint, not fixable here

## Key Implementation Details

- `pyautogui.PAUSE = 0` disables the default 0.1s pause after each pyautogui call (critical for speed)
- `pyautogui.FAILSAFE = False` prevents corner-trigger interrupts
- Separator lines (---, ===, ⸻) are typed as a visible `---` on their own line in Word/Excel modes
- Text input terminates on 2 consecutive empty lines (preserves paragraph breaks in pasted text)
- Single blank lines are preserved as paragraph breaks in typed output
- Smart quotes (`'`, `'`, `"`, `"`) normalized to straight quotes before typing
- Unicode bullet characters (`•`, `●`, `◦`, etc.) converted to dashes
- Bullet/numbered lists preserved with proper spacing. The space-insertion regexes only fire at line start and never before a digit — `$4.99`, `v1.3.1`, `**bold**` and `-5` must survive `clean_text()` untouched
- **ASCII-only mode** (`--ascii` / `[A]`): `to_ascii()` maps known symbols, strips accents, and turns the rest into `?`. Applied per cell in table mode, *after* `split_range_columns()`, so arrows still split ranges
- `get_multiline_input()` keeps reading past two blank lines when `stdin_has_pending()` says a paste is still arriving. The menu uses the same check, so a pasted document whose first line is `Text`, `Q` or `2024` isn't taken as a command
- `type_string()` pastes non-ASCII through `paste_via_clipboard()`. If the clipboard can't be read or our write never shows up, it types `to_ascii()` of the batch instead — never press Cmd+V on unconfirmed contents, that pastes the user's own clipboard
- `normalize_newlines()` turns `\r\n`, `\r`, Word's `\x0b` soft break etc. into `\n` and drops other control characters (pyautogui silently drops them, gluing words)
- The tests in `tests/redteam/` came from a Sonnet + Codex red-team pass; each one pins a real bug that was fixed

## Gotchas

- **Don't remove `empty_count` logic** in `get_multiline_input()` — it prevents pasted multi-paragraph text from terminating early at the first blank line
- **curl not urllib**: Version check uses `curl` via subprocess because Python 3.13 on macOS has SSL certificate verification failures with `urllib.request`
- **`__pycache__` clearing**: Auto-update runs `shutil.rmtree(__pycache__)` before `os.execv()` restart to prevent stale bytecode from caching the old VERSION
- **Header box width**: The print_header() box uses fixed-width lines (55 visible chars between `║` delimiters). When changing header text, count visible characters excluding ANSI escape codes
- **VERSION management**: Always update all three locations: `VERSION` constant in `lazy_typer.py`, README badge, and GitHub release (`gh release create`). **Bump `VERSION` last — as part of publishing the release, not while developing.** A local `VERSION` ahead of the published release is safe now (`version_tuple()` compares numerically), but keeping them in lockstep avoids confusing "current version" output
- **The auto-updater destroys uncommitted work**: `run_git_pull()` runs `git reset --hard origin/main`. It refuses unless `is_lazy_typer_checkout()` (repo root is the script dir and origin is `GITHUB_REPO`), the tree is clean (`has_uncommitted_changes()` treats a failing `git status` as dirty), HEAD is `main`, and no local commits are ahead of `origin/main` — do not remove those guards. Git runs through `git()`, which disables credential/host-key prompts. It exists because a `VERSION` bump combined with the old `latest != VERSION` check offered a phantom "downgrade update" and wiped 150 lines of uncommitted work when accepted. Version comparison must stay `>`, never `!=`
- **Arrow key input**: `arrow_key_select()` uses `tty.setcbreak()` + `os.read()` with 50ms `select.select()` timeout to distinguish Escape from arrow sequences. Falls back to numbered input if not a TTY
