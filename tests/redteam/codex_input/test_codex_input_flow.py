"""Adversarial input and CLI flow checks; the keyboard fixture prevents real typing."""

import builtins

import pytest

import lazy_typer as lt


def drive_main(monkeypatch, argv, answers):
    feed = iter(answers)

    def fake_input(*_):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError

    monkeypatch.setattr(builtins, "input", fake_input)
    monkeypatch.setattr(lt, "check_and_prompt_update", lambda: None)
    with pytest.raises(SystemExit) as exc:
        lt.main(argv)
    assert exc.value.code == 0


def test_menu_paste_starting_with_whitespace_keeps_first_line(
    keyboard, monkeypatch
):
    # The second document starts with an indentation-only line. It is still
    # part of the pasted document in Plain Text mode.
    drive_main(
        monkeypatch,
        ["--mode", "text"],
        ["1", "seed", "", "", "    ", "second line", "", "", "q"],
    )

    assert keyboard.text == "seed    \nsecond line"


def test_ascii_table_ready_count_includes_excel_safety_prefix(
    keyboard, monkeypatch
):
    ready = []
    monkeypatch.setattr(lt, "show_ready_message", lambda *args: ready.append(args))

    assert lt.run_typing_pass("x\t− item\ny\tz", "table", 1, ascii_only=True)

    assert keyboard.text == "x\t'- item\ny\tz\n"
    # Exclude the final Enter used to move to the next row; count all text
    # and separators entered before it.
    assert ready[0][0] == len(keyboard.text.rstrip("\n"))
