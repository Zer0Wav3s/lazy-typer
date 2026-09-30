"""Test harness: swaps pyautogui and the clipboard for in-memory fakes.

Nothing here sends real keystrokes. `keyboard.text` is what a plain text
editor would contain after the run; `keyboard.events` is the raw key log.
"""
import os
import subprocess
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import lazy_typer  # noqa: E402


class FakeKeyboard:
    def __init__(self):
        self.events = []
        self.text = ''
        self.clipboard = b'ORIGINAL CLIPBOARD'

    # pyautogui API used by lazy_typer
    def write(self, s, interval=0):
        for c in s:
            self.events.append(('write', c))
            self.text += '\n' if c in '\r\n' else c

    def press(self, key):
        self.events.append(('press', key))
        if key == 'enter':
            self.text += '\n'
        elif key == 'tab':
            self.text += '\t'

    def hotkey(self, *keys):
        self.events.append(('hotkey',) + keys)
        if keys == ('alt', 'enter'):
            self.text += '\n'
        elif keys == ('command', 'v'):
            self.text += self.clipboard.decode('utf-8')

    # clipboard via subprocess
    def run(self, real_run):
        def fake_run(cmd, *args, **kwargs):
            if cmd == ['pbcopy']:
                self.clipboard = kwargs.get('input') or b''
                return subprocess.CompletedProcess(cmd, 0, b'', b'')
            if cmd == ['pbpaste']:
                return subprocess.CompletedProcess(cmd, 0, self.clipboard, b'')
            return real_run(cmd, *args, **kwargs)
        return fake_run


@pytest.fixture
def keyboard(monkeypatch):
    kb = FakeKeyboard()
    monkeypatch.setattr(lazy_typer.pyautogui, 'write', kb.write)
    monkeypatch.setattr(lazy_typer.pyautogui, 'press', kb.press)
    monkeypatch.setattr(lazy_typer.pyautogui, 'hotkey', kb.hotkey)
    monkeypatch.setattr(lazy_typer.time, 'sleep', lambda *_: None)
    monkeypatch.setattr(lazy_typer.subprocess, 'run', kb.run(subprocess.run))
    return kb
