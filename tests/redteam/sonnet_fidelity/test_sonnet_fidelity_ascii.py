import lazy_typer as lt

SEP = lt.SEPARATOR_MARKER


def test_ascii_mode_keeps_unicode_separator_lines():
    out = lt.prepare_text("a\n⸻\nb", "word", ascii_only=True)
    assert out == "a\n" + SEP + "\nb"


def test_ascii_mode_box_drawing_separator(keyboard):
    lt.type_text("a\n─\nb", "word", ascii_only=True)
    assert "?" not in keyboard.text


def test_ascii_mode_bullet_without_space_matches_normal_mode():
    normal = lt.prepare_text("•item", "word")
    asc = lt.prepare_text("•item", "word", ascii_only=True)
    assert asc == normal == "- item"


def test_ascii_mode_latin_letters_without_decomposition():
    out = lt.to_ascii("Søren Straße Łódź")[0]
    assert "?" not in out


def test_ascii_mode_currency_symbols():
    out = lt.to_ascii("€5 £3 ¥10")[0]
    assert "?" not in out


def test_ascii_degree_sign_reads_naturally():
    assert lt.to_ascii("25°C")[0] != "25 degC"


def test_preview_lost_count_matches_what_is_typed(keyboard):
    # What would be typed contains a '?', so the preview's lost count should be > 0.
    text = "a\n⸻\nb"
    typed_lost = lt.to_ascii(text)[1]
    preview = lt.prepare_text(text, "word")
    preview_lost = lt.to_ascii(preview)[1]
    assert preview_lost == typed_lost
