"""Cleaning a dash bullet must not consume the following line break."""

import lazy_typer as lt


def test_standalone_unicode_dash_does_not_join_next_line():
    # A lone dash line is a separator (dropped at the very top); the point is
    # it must not fuse with the next line into "- Heading"
    assert lt.clean_text('—\nHeading') == 'Heading'
    assert lt.clean_text('a\n—\nHeading') == 'a\n' + lt.SEPARATOR_MARKER + '\nHeading'
