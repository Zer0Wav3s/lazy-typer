import lazy_typer as lt


def test_utf16_file_is_readable(tmp_path):
    p = tmp_path / 'u16.txt'
    p.write_text('hello world', encoding='utf-16')
    assert lt.read_text_file(str(p)) == 'hello world'
