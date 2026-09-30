"""Red-team tests for Excel Table/Grid mode. All typing goes through the fake keyboard."""
import lazy_typer as lt


def test_escaped_pipe_stays_inside_cell():
    rows = lt.parse_table('| expr | note |\n|---|---|\n| a \\| b | ok |')
    assert rows == [['expr', 'note'], ['a | b', 'ok']]


def test_dash_placeholder_row_is_not_an_alignment_row():
    rows = lt.parse_table('| name | qty |\n|---|---|\n| - | - |\n| bolt | 4 |')
    assert rows == [['name', 'qty'], ['-', '-'], ['bolt', '4']]


def test_blank_pipe_row_keeps_its_row_slot():
    rows = lt.parse_table('| a | b |\n|---|---|\n| | |\n| c | d |')
    assert rows == [['a', 'b'], ['', ''], ['c', 'd']]


def test_blank_tsv_row_keeps_its_row_slot():
    # Excel copies an empty row in a range as "\t\t"
    rows = lt.parse_table('a\tb\n\t\nc\td')
    assert rows == [['a', 'b'], ['', ''], ['c', 'd']]


def test_single_cell_tsv_row_is_not_dropped():
    rows = lt.parse_table('Section\nname\tqty\nbolt\t4')
    assert rows[0] == ['Section']
    assert len(rows) == 3


def test_quoted_tsv_cell_with_newline_and_quotes():
    # Excel quotes cells holding Alt+Enter line breaks / quotes when copying
    rows = lt.parse_table('"line1\nline2"\tz\nq\t"say ""hi"""')
    # In-cell line breaks are carried as <br>, which type_table types as Alt+Enter
    assert rows == [['line1<br>line2', 'z'], ['q', 'say "hi"']]


def test_stray_pipe_line_does_not_discard_tab_grid():
    rows = lt.parse_table('a\tb\n|x\ty\nc\td')
    assert rows == [['a', 'b'], ['|x', 'y'], ['c', 'd']]


def test_leading_arrow_bullet_does_not_insert_a_column(keyboard):
    # "→ done" is a note, not a date range (no start). It must not widen the grid.
    lt.type_text('a\tb\n\u2192 done\tz', 'table')
    assert keyboard.text.split('\n')[1].count('\t') == 1
