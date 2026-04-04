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
VERSION = "1.3.1"
GITHUB_REPO = "Zer0Wav3s/lazy-typer"

# Calculate base delay
BASE_DELAY = 60.0 / (WPM * CHARS_PER_WORD)

# Special marker for separator-based line breaks
SEPARATOR_MARKER = '\x00SEP\x00'


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
            subprocess.run(['pbcopy'], input=batch.encode('utf-8'), check=True)
            time.sleep(0.05)  # ensure clipboard is ready
            pyautogui.hotkey('command', 'v')
            time.sleep(0.15)  # ensure paste completes and Command key fully releases
            # Simulate natural typing delay for the batch length
            for _ in range(len(batch) - 1):
                time.sleep(calculate_delay())


def clean_text(text: str, preserve_whitespace: bool = False) -> str:
    """Clean up the text: remove tabs, fix list spacing, handle separators.

    If preserve_whitespace is True, only normalizes smart quotes and trims
    trailing blank lines — indentation and alignment are kept intact.
    """
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

    # Replace bullet point characters with dashes
    text = re.sub(r'[•◦▪▸►▻●○■□▶‣⁃∙]', '-', text)
    # Replace em/en dashes used as bullets (at start of line) with regular dashes
    text = re.sub(r'^[—–]\s*', '- ', text, flags=re.MULTILINE)
    # Replace remaining em/en dashes with regular dashes
    text = text.replace('—', '-').replace('–', '-')

    text = text.replace('\t', '')

    lines = text.split('\n')
    cleaned_lines = []

    i = 0
    while i < len(lines):
        stripped = lines[i].strip()

        is_separator = False
        if stripped:
            if stripped in ['⸻', '━', '─', '—']:
                is_separator = True
            elif len(stripped) >= 3 and all(c in '-_=~' for c in stripped):
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
    text = re.sub(r'(\d+\.)(?!\s)', r'\1 ', text)
    text = re.sub(r'^([-*])\s*(?=\S)', r'\1 ', text, flags=re.MULTILINE)

    return text.strip()


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


def type_text(text: str, app_mode: str):
    """Type the given text with human-like delays."""
    preserve_ws = app_mode in ("sql", "text")
    text = clean_text(text, preserve_whitespace=preserve_ws)

    if app_mode == "compress":
        lines = [line for line in text.split('\n') if line != SEPARATOR_MARKER and line != '']
        compressed = ' '.join(lines)
        compressed = re.sub(r'  +', ' ', compressed)
        compressed = re.sub(r'(?<=[a-z])\.(?=[A-Z])', '. ', compressed)

        time.sleep(0.3)
        type_string(compressed)
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
            next_line = lines[line_idx + 1] if line_idx + 1 < len(lines) else ""
            time.sleep(calculate_delay())
            if next_line != SEPARATOR_MARKER:
                type_newline(app_mode)
            time.sleep(calculate_delay())


# ═══════════════════════════════════════════════════════════════════════════════
# USER INPUT FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_multiline_input(first_line: str = None) -> str:
    """Collect multiline text input until two consecutive empty lines."""
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
    while True:
        try:
            line = input()
            if line == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append(line)  # preserve single blank lines (paragraph breaks)
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

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
        print(f"  {Colors.YELLOW}[E]{Colors.RESET}  {Colors.WHITE}Microsoft Excel{Colors.RESET}")
        print(f"       {Colors.GRAY}Alt+Enter for in-cell line breaks{Colors.RESET}")
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

        choice = input(f"\n{Colors.CYAN}Enter choice (W/E/T/S/C):{Colors.RESET} ").strip().lower()

        if choice in ('w', 'word'):
            print_success("Mode set: Microsoft Word")
            return "word"
        elif choice in ('e', 'excel'):
            print_success("Mode set: Microsoft Excel")
            return "excel"
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
            print_error("Invalid choice. Please enter W, E, T, S, or C.")


def show_ready_message(char_count: int, word_count: int, estimated_time: float):
    """Show the ready message before typing."""
    print()
    print_divider()
    print(f"  {Colors.WHITE}{Colors.BOLD}📊 Ready to type:{Colors.RESET}")
    print(f"     {Colors.CYAN}{char_count}{Colors.RESET} characters  •  {Colors.CYAN}~{word_count}{Colors.RESET} words")
    print(f"     {Colors.GRAY}Estimated time: ~{estimated_time:.1f} seconds{Colors.RESET}")
    print_divider()
    print()
    print(f"  {Colors.YELLOW}{Colors.BOLD}👉 Switch to your target application now!{Colors.RESET}")


def show_done_message(app_mode: str):
    """Show the completion message with current mode."""
    mode_display = {"word": "Word", "excel": "Excel", "text": "Plain Text", "sql": "SQL / Code", "compress": "Compress"}
    mode_name = mode_display.get(app_mode, app_mode)
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


def show_menu(countdown_seconds: int, app_mode: str):
    """Show the options menu."""
    mode_display = {"word": "Word", "excel": "Excel", "text": "Plain Text", "sql": "SQL / Code", "compress": "Compress"}
    mode_name = mode_display.get(app_mode, app_mode)
    print()
    print(f"{Colors.CYAN}{Colors.BOLD}What's next?{Colors.RESET}")
    print_divider()
    print(f"  {Colors.YELLOW}[Enter]{Colors.RESET}  Type more text")
    print(f"  {Colors.YELLOW}[W/E/T/S/C]{Colors.RESET}  Switch mode ({mode_name})")
    print(f"  {Colors.YELLOW}[T]{Colors.RESET}      Change countdown timer ({countdown_seconds}s)")
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
        tag = data.get("tag_name", "")
        latest = tag.lstrip("v")
        html_url = data.get("html_url", "")

        if latest and latest != VERSION:
            return (latest, html_url)
        return None
    except (subprocess.TimeoutExpired, json.JSONDecodeError,
            KeyError, OSError, ValueError):
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
        choice = input("Choice: ").strip()
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

            if b in (b'\r', b'\n'):
                break
            if b == b'\x03':
                raise KeyboardInterrupt

            if b == b'\x1b':
                if sel.select([fd], [], [], 0.05)[0]:
                    b2 = os.read(fd, 1)
                    if b2 == b'[' and sel.select([fd], [], [], 0.05)[0]:
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


def run_git_pull():
    """Fetch and reset to origin/main. Returns True on success."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    try:
        fetch = subprocess.run(
            ["git", "fetch", "origin"],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        if fetch.returncode != 0:
            print_error(f"Update failed: {fetch.stderr.strip()}")
            return False

        reset = subprocess.run(
            ["git", "reset", "--hard", "origin/main"],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=10
        )
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

def main():
    """Main loop for the Lazy Typer."""
    check_and_prompt_update()
    print_header()
    app_mode = get_app_mode()
    countdown_seconds = get_countdown()

    while True:
        text = get_multiline_input()

        if text.lower() == 'quit':
            print()
            print_info("Goodbye! 👋")
            sys.exit(0)

        if not text.strip():
            print_warning("No text entered. Try again or type 'quit' to exit.")
            continue

        preserve_ws = app_mode == "sql"
        cleaned = clean_text(text, preserve_whitespace=preserve_ws)
        char_count = len(cleaned)
        word_count = len(cleaned.split())
        estimated_time = char_count * BASE_DELAY

        show_ready_message(char_count, word_count, estimated_time)
        countdown(countdown_seconds)
        type_text(text, app_mode)
        show_done_message(app_mode)
        show_menu(countdown_seconds, app_mode)

        choice = input(f"\n{Colors.CYAN}Your choice:{Colors.RESET} ").strip()

        if choice.lower() == 'q':
            print()
            print_info("Goodbye! 👋")
            sys.exit(0)
        elif choice.lower() in ('w', 'word'):
            app_mode = "word"
            print_success("Mode set: Microsoft Word")
        elif choice.lower() in ('e', 'excel'):
            app_mode = "excel"
            print_success("Mode set: Microsoft Excel")
        elif choice.lower() in ('t', 'text'):
            app_mode = "text"
            print_success("Mode set: Plain Text (exact copy)")
        elif choice.lower() in ('s', 'sql'):
            app_mode = "sql"
            print_success("Mode set: SQL / Code (preserves formatting)")
        elif choice.lower() in ('c', 'compress'):
            app_mode = "compress"
            print_success("Mode set: Compress (single line)")
        elif choice.lower() == 'm':
            app_mode = get_app_mode()
        elif choice.lower() == 't':
            countdown_seconds = get_countdown()
        elif choice == '':
            pass
        else:
            text = get_multiline_input(first_line=choice)
            if text.strip():
                cleaned = clean_text(text, preserve_whitespace=(app_mode in ("sql", "text")))
                char_count = len(cleaned)
                word_count = len(cleaned.split())
                estimated_time = char_count * BASE_DELAY
                show_ready_message(char_count, word_count, estimated_time)
                countdown(countdown_seconds)
                type_text(text, app_mode)
                show_done_message(app_mode)
            continue


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print()
        print()
        print_info("Interrupted. Goodbye! 👋")
        sys.exit(0)
