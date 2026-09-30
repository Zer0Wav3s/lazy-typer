"""Adversarial table-mode checks. Typing tests use the fake keyboard fixture."""

import lazy_typer as lt


def test_markdown_table_without_outer_pipes_keeps_columns(keyboard):
    source = 'Name | Qty\n--- | ---\nBolt | 4'
    mode = lt.resolve_mode(source, 'excel')
    lt.type_text(source, mode)
    assert keyboard.text == 'Name\tQty\nBolt\t4\n'


def test_two_single_column_pipe_lines_stay_in_one_excel_cell(keyboard):
    source = '| first line\n| second line'
    mode = lt.resolve_mode(source, 'excel')
    lt.type_text(source, mode)
    assert keyboard.text == '| first line\n| second line'
    assert mode == 'excel'


def test_spaced_ascii_hyphen_splits_date_range_column():
    rows = [['Task', 'Dates'], ['Build', '21 Sep - 12 Oct'], ['Test', '26 Oct']]
    assert lt.split_range_columns(rows) == [
        ['Task', 'Dates', ''],
        ['Build', '21 Sep', '12 Oct'],
        ['Test', '26 Oct', ''],
    ]


def test_non_date_arrow_does_not_split_status_column(keyboard):
    source = 'Task\tStatus\nBuild\tPending → Done'
    lt.type_text(source, 'table')
    assert keyboard.text == 'Task\tStatus\nBuild\tPending - Done\n'


def test_signed_scientific_number_remains_numeric():
    assert lt.excel_safe('-1.2E+3') == '-1.2E+3'
