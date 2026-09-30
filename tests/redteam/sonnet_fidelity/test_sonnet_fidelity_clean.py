import lazy_typer as lt

SEP = lt.SEPARATOR_MARKER


def test_tab_between_words_is_not_glued_together():
    # Tabs (TOC entries, pasted table rows) must become a space, not vanish.
    assert lt.clean_text("Name\tAge") == "Name Age"


def test_lone_emdash_separator_line_survives():
    # '—' alone on a line is listed as a separator, but the bullet regex's \s*
    # swallows the newline and fuses it with the next line.
    assert lt.clean_text("a\n—\nb") == "a\n" + SEP + "\nb"


def test_lone_endash_line_does_not_eat_paragraph_break():
    out = lt.clean_text("a\n–\n\nb")
    assert "- b" not in out


def test_compress_does_not_split_dotted_identifiers(keyboard):
    lt.type_text("Call Node.Js or Math.Floor(x) on System.Console", "compress")
    assert keyboard.text == "Call Node.Js or Math.Floor(x) on System.Console"
