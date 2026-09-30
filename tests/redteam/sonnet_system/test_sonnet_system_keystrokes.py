import subprocess

import pytest

import lazy_typer


@pytest.mark.parametrize("mode", ["word", "text", "sql", "excel", "compress"])
def test_control_chars_never_sent_to_pyautogui_write(keyboard, mode):
    # Word soft line breaks copy out as \x0b (VT). pyautogui silently drops
    # keys it has no mapping for, so the two words get glued together.
    lazy_typer.type_text("foo\x0bbar", mode)
    written = [e[1] for e in keyboard.events if e[0] == 'write']
    assert all(32 <= ord(c) < 127 for c in written), written
    assert 'foobar' not in keyboard.text


def test_clipboard_subprocess_calls_have_timeout(keyboard, monkeypatch):
    calls = []
    inner = subprocess.run

    def spy(cmd, *a, **kw):
        calls.append((cmd, kw))
        return inner(cmd, *a, **kw)

    monkeypatch.setattr(lazy_typer.subprocess, 'run', spy)
    lazy_typer.type_string("café")
    pb = [(c, kw) for c, kw in calls if c and c[0] in ('pbcopy', 'pbpaste')]
    assert pb
    assert all(kw.get('timeout') for _, kw in pb), [c for c, kw in pb if not kw.get('timeout')]
