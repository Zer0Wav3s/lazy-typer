import pytest
import lazy_typer as lt


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


def test_pasted_text_starting_with_big_number_is_not_swallowed(keyboard, monkeypatch):
    # mode, countdown, first paste, menu gets pasted "2024" line (>10 => countdown prompt),
    # rest of paste lines follow.
    run_main(monkeypatch, [], ['t', '1', 'hello', '', '', '2024', 'Revenue grew', '', ''])
    assert '2024' in keyboard.text
    assert 'Revenue grew' in keyboard.text


def test_pasted_first_line_equal_to_mode_word_is_not_swallowed(keyboard, monkeypatch):
    # A pasted doc whose first line is the heading "Text" must not be read as
    # the menu's mode command. pytest's stdin isn't a TTY, so simulate "more
    # paste is queued" for the menu read only.
    state = {'after_menu': False}
    feed = iter(['t', '1', 'hello', '', '', 'Text', 'body line', '', ''])

    def fake_input(prompt=''):
        state['after_menu'] = 'Your choice' in prompt
        try:
            return next(feed)
        except StopIteration:
            raise EOFError
    monkeypatch.setattr('builtins.input', fake_input)
    monkeypatch.setattr(lt, 'stdin_has_pending', lambda *a: state['after_menu'])
    monkeypatch.setattr(lt, 'check_and_prompt_update', lambda: None)
    with pytest.raises(SystemExit):
        lt.main([])
    assert 'Text\nbody line' in keyboard.text


def test_menu_superscript_digit_does_not_crash(keyboard, monkeypatch):
    # '²'.isdigit() is True but int('²') raises ValueError -> traceback
    try:
        run_main(monkeypatch, [], ['t', '1', 'hello', '', '', '²'])
    except ValueError as e:
        pytest.fail(f"menu crashed with ValueError: {e}")


def test_file_containing_only_quit_is_typed_not_treated_as_exit(keyboard, monkeypatch, tmp_path):
    p = tmp_path / 'q.txt'
    p.write_text('quit')
    run_main(monkeypatch, [str(p), '--mode', 'text'], ['1'])
    assert keyboard.text == 'quit'


def test_separator_only_text_does_not_claim_done(keyboard, monkeypatch, capsys):
    run_main(monkeypatch, [], ['w', '1', '---', '', ''])
    out = capsys.readouterr().out
    assert keyboard.text == ''
    assert 'Done! Text has been typed' not in out
