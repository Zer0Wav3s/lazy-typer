"""Compression may remove line breaks, but must retain the content of lines."""

import lazy_typer as lt


def test_compress_preserves_dotted_identifier(keyboard):
    lt.type_text('Call api.Client now', 'compress')
    assert keyboard.text == 'Call api.Client now'


def test_compress_preserves_spaces_inside_quoted_value(keyboard):
    lt.type_text("SELECT 'a  b'", 'compress')
    assert keyboard.text == "SELECT 'a  b'"
