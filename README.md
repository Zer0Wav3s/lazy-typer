<div align="center">

# Lazy Typer

**Human-Like Typing Simulation for Word, Excel, and More**

[![Version](https://img.shields.io/badge/Version-1.3.1-red?logo=github&logoColor=white)](https://github.com/Zer0Wav3s/lazy-typer/releases)
[![Python](https://img.shields.io/badge/Python-3.6+-blue?logo=python&logoColor=white)](https://www.python.org)
[![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-keyboard_automation-green?logo=python&logoColor=white)](https://pyautogui.readthedocs.io)

</div>

> **Disclaimer**: This project is experimental and provided as-is. The author assumes no responsibility for how this script is used. By using this tool, you acknowledge that you are solely responsible for ensuring your use complies with all applicable policies, terms of service, and regulations.

## Features

- **Human-like typing** at ~250 WPM with natural variation
- **Five application modes**: Word, Excel, Plain Text, SQL/Code, and Compress
- **Unicode support**: Handles non-ASCII characters (circled letters, symbols, etc.) via clipboard paste
- **Adjustable countdown timer**: Set between 1-10 seconds
- **Quick mode switching**: Press W/E/T/S/C to change modes instantly
- **Smart text cleaning**: Removes tabs, handles separators, preserves lists
- **Automatic update check**: Notifies you when a new version is available
- **Continuous operation**: Loop for multiple text entries

## Installation

```bash
# Clone the repository
git clone https://github.com/Zer0Wav3s/lazy-typer.git
cd lazy-typer

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python lazy_typer.py
```

1. Select your application mode (Word, Excel, Plain Text, SQL/Code, or Compress)
2. Set your countdown timer (1-10 seconds, or Enter for default)
3. Paste or type your text
4. Press Enter 3 times to confirm
5. Switch to your target application during the countdown
6. Text will be typed automatically

After typing completes, use these shortcuts:
- **W/E/T/S/C** - Switch mode directly
- **T** - Change countdown timer
- **Q** - Quit

## Modes

| Mode | Newline Behavior | Use Case |
|------|------------------|----------|
| **Word** | Enter key | Microsoft Word, text editors |
| **Excel** | Alt+Enter | In-cell line breaks in Excel |
| **Plain Text** | Enter key | Exact copy with all formatting preserved |
| **SQL / Code** | Enter + auto-indent clearing | SQL editors, IDEs with auto-indent |
| **Compress** | No line breaks | Single-line output |

### Mode Details

- **Word**: Standard typing with Enter for newlines. Smart text cleaning converts separators, normalizes quotes, and handles bullet lists. Separator lines (---, ===) are typed as visible `---` text.
- **Excel**: Same as Word but uses Alt+Enter for in-cell line breaks.
- **Plain Text**: Types everything exactly as entered — no separator conversion, no bullet handling. Only smart quotes are normalized. Ideal when you want a 1:1 copy of your input.
- **SQL / Code**: Preserves indentation and alignment. After each Enter, clears any auto-indent the target editor may add, then types the exact leading spaces from your original text. Perfect for pasting formatted SQL or code into editors that auto-indent.
- **Compress**: Joins all lines into a single line with no line breaks. Useful for single-line input fields.

## Configuration

Edit the constants in `lazy_typer.py` to customize default behavior:

```python
WPM = 250                    # Words per minute
VARIATION = 0.45             # Typing speed variation (±45%)
DEFAULT_COUNTDOWN = 5        # Default countdown (adjustable at runtime)
WORD_PAUSE_MULTIPLIER = 1.08 # Extra pause between words
```

## Text Processing

The script automatically:

- Removes all tab characters
- Converts separator lines (---, ===, etc.) to line breaks
- Preserves paragraph breaks (blank lines between paragraphs)
- Normalizes smart quotes/apostrophes to straight versions
- Converts bullet point characters (•, ●, ◦, etc.) to dashes
- Converts em/en dashes used as bullets to regular dashes
- Ensures proper spacing after numbered lists (1. 2. 3.)
- Preserves bullet points (-, *, etc.)
- Handles Unicode characters via batched clipboard paste

> **Note**: Plain Text and SQL/Code modes skip most text processing (bullet conversion, tab removal, separator handling) to preserve your original formatting. Only smart quote normalization is applied.

## Requirements

- Python 3.6+
- pyautogui
- macOS (uses `pbcopy` for Unicode clipboard support)

## License

MIT
