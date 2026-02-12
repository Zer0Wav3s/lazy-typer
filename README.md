<div align="center">

# Lazy Typer

**Human-Like Typing Simulation for Word, Excel, and More**

[![Version](https://img.shields.io/badge/Version-1.2.1-red?logo=github&logoColor=white)](https://github.com/Zer0Wav3s/lazy-typer/releases)
[![Python](https://img.shields.io/badge/Python-3.6+-blue?logo=python&logoColor=white)](https://www.python.org)
[![PyAutoGUI](https://img.shields.io/badge/PyAutoGUI-keyboard_automation-green?logo=python&logoColor=white)](https://pyautogui.readthedocs.io)

</div>

> **Disclaimer**: This project is experimental and provided as-is. The author assumes no responsibility for how this script is used. By using this tool, you acknowledge that you are solely responsible for ensuring your use complies with all applicable policies, terms of service, and regulations.

## Features

- **Human-like typing** at ~250 WPM with natural variation
- **Three application modes**: Word, Excel, and Compress
- **Adjustable countdown timer**: Set between 1-10 seconds
- **Quick mode switching**: Press W/E/C to change modes instantly
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

1. Select your application mode (Word, Excel, or Compress)
2. Set your countdown timer (1-10 seconds, or Enter for default)
3. Paste or type your text
4. Press Enter 3 times to confirm
5. Switch to your target application during the countdown
6. Text will be typed automatically

After typing completes, use these shortcuts:
- **W/E/C** - Switch mode directly
- **T** - Change countdown timer
- **Q** - Quit

## Modes

| Mode | Newline Behavior | Use Case |
|------|------------------|----------|
| **Word** | Enter key | Microsoft Word, text editors |
| **Excel** | Alt+Enter | In-cell line breaks in Excel |
| **Compress** | No line breaks | Single-line output |

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
- Ensures proper spacing after numbered lists (1. 2. 3.)
- Preserves bullet points (-, *, etc.)

## Requirements

- Python 3.6+
- pyautogui

## License

MIT
