"""Regression targets for the Unicode clipboard paste path."""

import subprocess

import lazy_typer as lt


def test_failed_initial_pbpaste_does_not_erase_existing_clipboard(keyboard, monkeypatch):
    original_run = lt.subprocess.run
    reads = 0

    def fail_first_clipboard_read(cmd, *args, **kwargs):
        nonlocal reads
        if cmd == ['pbpaste']:
            reads += 1
            if reads == 1:
                raise subprocess.CalledProcessError(1, cmd)
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(lt.subprocess, 'run', fail_first_clipboard_read)

    lt.type_string('é')

    assert keyboard.clipboard == b'ORIGINAL CLIPBOARD'


def test_unconfirmed_clipboard_write_never_pastes_old_contents(keyboard, monkeypatch):
    original_run = lt.subprocess.run
    clock = iter([0.0, 0.6, 1.2])

    def clipboard_write_not_yet_committed(cmd, *args, **kwargs):
        if cmd == ['pbcopy'] and kwargs.get('input') == 'é'.encode():
            return subprocess.CompletedProcess(cmd, 0, b'', b'')
        return original_run(cmd, *args, **kwargs)

    monkeypatch.setattr(lt.subprocess, 'run', clipboard_write_not_yet_committed)
    monkeypatch.setattr(lt.time, 'monotonic', lambda: next(clock))

    lt.type_string('é')

    # Never Cmd+V the user's own clipboard; fall back to typing the ASCII form
    assert not any(e[0] == 'hotkey' and 'command' in e for e in keyboard.events)
    assert keyboard.text == 'e'
    assert keyboard.clipboard == b'ORIGINAL CLIPBOARD'
