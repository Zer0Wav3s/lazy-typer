import os

import pytest

import lazy_typer as lt

SKILL = os.path.expanduser('~/.claude/skills/plainspoken/SKILL.md')


# ── clean_text ────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('src, expected', [
    ('Price is $4.99 in v1.3.1', 'Price is $4.99 in v1.3.1'),
    ('**bold** start', '**bold** start'),
    ('-5 degrees', '-5 degrees'),
    ('--> arrow', '--> arrow'),
    ('•item', '- item'),
    ('  • item', '- item'),
    ('1.First', '1. First'),
    ('-    spaced', '- spaced'),
    ('a\r\nb', 'a\nb'),
])
def test_clean_text(src, expected):
    assert lt.clean_text(src) == expected


def test_word_separator_gets_its_own_line(keyboard):
    lt.type_text('Hello\n---\nWorld', 'word')
    assert keyboard.text == 'Hello\n---\nWorld'


# ── plain text mode ───────────────────────────────────────────────────────────

def test_plain_text_is_exact(keyboard):
    src = '---\nname: x\n---\n\n# Head\n\n| a | b |\n|---|---|\n- item\n  indented'
    lt.type_text(src, 'text')
    assert keyboard.text == src


def test_plain_text_pastes_unicode_and_restores_clipboard(keyboard):
    lt.type_text('wait… now — go', 'text')
    assert keyboard.text == 'wait… now — go'
    assert keyboard.clipboard == b'ORIGINAL CLIPBOARD'


def test_ascii_only_never_touches_clipboard(keyboard):
    lt.type_text('wait… now — go “quoted” café', 'text', ascii_only=True)
    assert keyboard.text == 'wait... now - go "quoted" cafe'
    assert not any(e[0] == 'hotkey' and 'command' in e for e in keyboard.events)


@pytest.mark.skipif(not os.path.exists(SKILL), reason='plainspoken skill not installed')
@pytest.mark.parametrize('ascii_only', [False, True])
def test_plainspoken_skill_round_trips(keyboard, ascii_only):
    src = open(SKILL, encoding='utf-8').read()
    lt.type_text(src, 'text', ascii_only=ascii_only)
    expected = lt.clean_text(src, preserve_whitespace=True)
    if ascii_only:
        expected = lt.to_ascii(expected)[0]
    assert keyboard.text == expected


# ── to_ascii ──────────────────────────────────────────────────────────────────

def test_to_ascii_counts_unmappable():
    out, lost = lt.to_ascii('ok → 日本 é')
    assert out == 'ok -> ?? e'
    assert lost == 2


# ── Excel ─────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('cell, expected', [
    ('- item', "'- item"),
    ('+1 555 0100', "'+1 555 0100"),
    ('@home', "'@home"),
    ('-5', '-5'),
    ('+3.2', '+3.2'),
    ('-12%', '-12%'),
    ('=SUM(A1:A2)', '=SUM(A1:A2)'),
    ('plain', 'plain'),
    ('', ''),
])
def test_excel_safe(cell, expected):
    assert lt.excel_safe(cell) == expected


def test_excel_single_cell_bullet_list_is_not_a_formula(keyboard):
    lt.type_text('- one\n- two', 'excel')
    assert keyboard.text.startswith("'- one")


def test_table_mode_grid(keyboard):
    lt.type_text('a\tb\n- x\t2', 'table')
    assert keyboard.text == "a\tb\n'- x\t2\n"


def test_table_autocomplete_cleared_only_after_text(keyboard):
    lt.type_text('a\t\tc\nd\te\tf', 'table')
    presses = [e[1] for e in keyboard.events if e[0] == 'press']
    # a DEL tab | (empty) tab | c DEL enter | ...
    assert presses[:5] == ['delete', 'tab', 'tab', 'delete', 'enter']


def test_range_split_keeps_unspaced_dates():
    rows = lt.split_range_columns([['T', '21-Sep → 12-Oct'], ['U', '26-Oct-26']])
    assert rows == [['T', '21-Sep', '12-Oct'], ['U', '26-Oct-26', '']]


# ── version / input ───────────────────────────────────────────────────────────

def test_version_tuple_trailing_zero():
    assert lt.version_tuple('1.3') == lt.version_tuple('1.3.0')
    assert lt.version_tuple('1.10') > lt.version_tuple('1.9')


def test_multiline_input_eof_returns_none(monkeypatch):
    def eof(*_):
        raise EOFError
    monkeypatch.setattr('builtins.input', eof)
    assert lt.get_multiline_input() is None


def test_multiline_input_strips_trailing_blanks(monkeypatch):
    feed = iter(['quit', '', ''])
    monkeypatch.setattr('builtins.input', lambda *_: next(feed))
    assert lt.get_multiline_input() == 'quit'


def test_read_text_file_normalizes(tmp_path):
    p = tmp_path / 'f.md'
    p.write_bytes('﻿a\r\nb\r\n'.encode('utf-8'))
    assert lt.read_text_file(str(p)) == 'a\nb\n'


def test_read_text_file_missing_exits(tmp_path):
    with pytest.raises(SystemExit):
        lt.read_text_file(str(tmp_path / 'nope.txt'))


# ── main flow ─────────────────────────────────────────────────────────────────

def run_main(monkeypatch, argv, answers):
    feed = iter(answers)

    def fake_input(*_):
        try:
            return next(feed)
        except StopIteration:
            raise EOFError
    monkeypatch.setattr('builtins.input', fake_input)
    monkeypatch.setattr(lt, 'check_and_prompt_update', lambda: None)
    with pytest.raises(SystemExit) as exc:
        lt.main(argv)
    return exc.value.code


def test_main_types_file_then_exits_on_eof(keyboard, monkeypatch, tmp_path):
    p = tmp_path / 'skill.md'
    p.write_text('# Title\n\nwait… ok\n', encoding='utf-8')
    code = run_main(monkeypatch, [str(p), '--mode', 'text', '--ascii'], ['1'])
    assert code == 0
    assert keyboard.text == '# Title\n\nwait... ok'


def test_main_menu_digit_sets_countdown_directly(keyboard, monkeypatch, capsys):
    # mode prompt, countdown, paste, menu "3", then EOF at the paste prompt
    run_main(monkeypatch, [], ['t', '1', 'hi', '', '', '3'])
    out = capsys.readouterr().out
    assert 'Countdown set: 3 seconds' in out
    assert out.count('Set Countdown Timer') == 1


def test_main_quit_word_exits_without_typing(keyboard, monkeypatch):
    assert run_main(monkeypatch, [], ['t', '1', 'quit', '', '']) == 0
    assert keyboard.text == ''


def test_real_checkout_is_recognised_for_updates():
    # Read-only git calls; guards against the identity check refusing every update
    repo = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    assert lt.is_lazy_typer_checkout(repo)
    assert not lt.is_lazy_typer_checkout(os.path.join(repo, 'tests'))
