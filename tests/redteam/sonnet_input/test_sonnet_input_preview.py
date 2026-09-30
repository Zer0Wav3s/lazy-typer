import lazy_typer as lt


def test_preview_char_count_matches_typed_for_separator(keyboard, monkeypatch):
    seen = {}
    real = lt.show_ready_message

    def spy(char_count, *a, **k):
        seen['n'] = char_count
        return real(char_count, *a, **k)
    monkeypatch.setattr(lt, 'show_ready_message', spy)
    lt.run_typing_pass('a\n---\nb', 'word', 1)
    assert seen['n'] == len(keyboard.text)


def test_table_accented_cells_warn_about_clipboard(keyboard, capsys):
    lt.run_typing_pass('a\tcafé\nb\tc', 'table', 1)
    out = capsys.readouterr().out
    assert 'pasted via the clipboard' in out
