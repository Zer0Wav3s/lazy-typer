"""Updater safety checks use only subprocess fakes and a throwaway path."""

import subprocess

import lazy_typer as lt


def test_git_status_failure_is_treated_as_dirty(tmp_path, monkeypatch):
    def failed_status(cmd, **kwargs):
        assert cmd == ['git', 'status', '--porcelain']
        assert kwargs['cwd'] == str(tmp_path)
        return subprocess.CompletedProcess(cmd, 128, '', 'fatal: not a git repository')

    monkeypatch.setattr(lt.subprocess, 'run', failed_status)

    assert lt.has_uncommitted_changes(str(tmp_path)) is True


def test_updater_never_resets_after_git_status_failure(tmp_path, monkeypatch):
    commands = []

    def fake_git(cmd, **kwargs):
        assert kwargs['cwd'] == str(tmp_path)
        commands.append(cmd)
        if cmd == ['git', 'status', '--porcelain']:
            return subprocess.CompletedProcess(cmd, 128, '', 'fatal: status unavailable')
        if cmd == ['git', 'rev-parse', '--abbrev-ref', 'HEAD']:
            return subprocess.CompletedProcess(cmd, 0, 'main\n', '')
        if cmd == ['git', 'rev-list', '--count', 'origin/main..HEAD']:
            return subprocess.CompletedProcess(cmd, 0, '0\n', '')
        return subprocess.CompletedProcess(cmd, 0, '', '')

    monkeypatch.setattr(lt, '__file__', str(tmp_path / 'lazy_typer.py'))
    monkeypatch.setattr(lt.subprocess, 'run', fake_git)

    assert lt.run_git_pull() is False
    assert not any(cmd[:3] == ['git', 'reset', '--hard'] for cmd in commands)


def test_prerelease_tag_is_not_offered_as_stable_update(monkeypatch):
    def fake_curl(cmd, **kwargs):
        assert cmd[0] == 'curl'
        return subprocess.CompletedProcess(
            cmd, 0,
            '{"tag_name": "v1.3.2-rc.1", "html_url": "https://example.invalid/rc"}',
            '',
        )

    monkeypatch.setattr(lt.subprocess, 'run', fake_curl)

    assert lt.check_for_latest_version() is None


def test_non_tty_update_menu_defaults_to_continue_on_eof(monkeypatch):
    monkeypatch.setattr(lt.sys.stdin, 'isatty', lambda: False)

    def eof(*_):
        raise EOFError

    monkeypatch.setattr('builtins.input', eof)

    assert lt.arrow_key_select(['Update Now', 'Continue']) == 1
