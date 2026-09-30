import lazy_typer as lt


def test_word_separator_after_dash_list_exits_auto_list(keyboard):
    lt.type_text("- a\n- b\n---\nc", "word")
    ev = keyboard.events
    # find the '---' write and count Enters between 'b' and first '-' of separator
    s = [i for i, e in enumerate(ev) if e == ('write', 'b')][0]
    d = [i for i, e in enumerate(ev) if i > s and e == ('write', '-')][0]
    enters = [e for e in ev[s:d] if e == ('press', 'enter')]
    assert len(enters) == 2, "Word auto-list needs an extra Enter before the ---"


def test_excel_single_cell_clears_autocomplete(keyboard):
    lt.type_text("Ap", "excel")
    assert keyboard.events[-1] == ('press', 'delete')
