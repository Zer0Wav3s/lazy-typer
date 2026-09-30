"""The pre-typing count should describe what the app will receive."""

import lazy_typer as lt


def test_compress_ready_count_matches_typed_characters(keyboard, monkeypatch):
    ready_counts = []
    monkeypatch.setattr(lt, 'countdown', lambda *_: None)
    monkeypatch.setattr(
        lt, 'show_ready_message',
        lambda char_count, *_args, **_kwargs: ready_counts.append(char_count),
    )

    assert lt.run_typing_pass('before\n===\nafter', 'compress', 1)
    assert ready_counts == [len(keyboard.text)]
