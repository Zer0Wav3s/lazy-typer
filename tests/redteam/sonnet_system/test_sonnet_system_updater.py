import io
import os
import subprocess
import sys

import pytest

import lazy_typer

REAL_RUN = subprocess.run


def git(cwd, *args):
    return REAL_RUN(['git', *args], cwd=cwd, capture_output=True, text=True, check=True).stdout.strip()


@pytest.fixture
def gitenv(monkeypatch):
    for k, v in dict(GIT_AUTHOR_NAME='t', GIT_AUTHOR_EMAIL='t@t', GIT_COMMITTER_NAME='t',
                     GIT_COMMITTER_EMAIL='t@t', GIT_CONFIG_GLOBAL=os.devnull,
                     GIT_CONFIG_SYSTEM=os.devnull).items():
        monkeypatch.setenv(k, v)


def test_updater_refuses_unrelated_repo_containing_script(tmp_path, monkeypatch, gitenv):
    # lazy_typer.py sits in a subfolder of some OTHER repo whose origin is not
    # lazy-typer. The updater resets that whole repo to its origin/main.
    origin = tmp_path / 'origin.git'
    git(tmp_path, 'init', '-q', '--bare', '-b', 'main', str(origin))
    work = tmp_path / 'work'
    git(tmp_path, 'clone', '-q', str(origin), str(work))
    (work / 'sub').mkdir()
    (work / 'sub' / 'lazy_typer.py').write_text('x')
    git(work, 'add', '-A'); git(work, 'commit', '-qm', 'one'); git(work, 'push', '-q', 'origin', 'HEAD:main')
    other = tmp_path / 'other'
    git(tmp_path, 'clone', '-q', str(origin), str(other))
    (other / 'new.txt').write_text('n')
    git(other, 'add', '-A'); git(other, 'commit', '-qm', 'two'); git(other, 'push', '-q', 'origin', 'HEAD:main')
    before = git(work, 'rev-parse', 'HEAD')

    monkeypatch.setattr(lazy_typer, '__file__', str(work / 'sub' / 'lazy_typer.py'))
    lazy_typer.run_git_pull()
    assert git(work, 'rev-parse', 'HEAD') == before


def test_git_fetch_cannot_prompt_for_credentials(monkeypatch):
    seen = []

    def fake(cmd, *a, **kw):
        seen.append((cmd, kw))
        if cmd[:2] == ['git', 'fetch']:
            return subprocess.CompletedProcess(cmd, 1, '', 'fail')
        return subprocess.CompletedProcess(cmd, 0, '', '')

    monkeypatch.setattr(lazy_typer.subprocess, 'run', fake)
    monkeypatch.setattr(lazy_typer, 'is_lazy_typer_checkout', lambda d: True)
    lazy_typer.run_git_pull()
    kw = [k for c, k in seen if c[:2] == ['git', 'fetch']][0]
    assert kw.get('stdin') == subprocess.DEVNULL or (kw.get('env') or {}).get('GIT_TERMINAL_PROMPT') == '0'


def test_status_failure_is_treated_as_dirty(monkeypatch):
    monkeypatch.setattr(lazy_typer.subprocess, 'run',
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 128, '', 'fatal: index corrupt'))
    assert lazy_typer.has_uncommitted_changes('/nonexistent') is True


def test_deeply_nested_json_does_not_crash_version_check(monkeypatch):
    monkeypatch.setattr(lazy_typer.subprocess, 'run',
                        lambda cmd, *a, **k: subprocess.CompletedProcess(cmd, 0, '[' * 200000, ''))
    assert lazy_typer.check_for_latest_version() is None


def test_non_tty_stdin_not_consumed_as_update_answer(monkeypatch):
    called = []
    monkeypatch.setattr(lazy_typer, 'check_for_latest_version', lambda: ('9.9.9', 'u'))
    monkeypatch.setattr(lazy_typer, 'run_git_pull', lambda: called.append(1) or False)
    stdin = io.StringIO("1\nrest of the pasted text\n")
    monkeypatch.setattr(sys, 'stdin', stdin)
    lazy_typer.check_and_prompt_update()
    assert not called
    assert stdin.read() == "1\nrest of the pasted text\n"


def test_arrow_select_survives_closed_stdin(monkeypatch):
    monkeypatch.setattr(sys, 'stdin', io.StringIO(''))
    assert lazy_typer.arrow_key_select(['Update Now', 'Continue']) == 1


def test_arrow_select_does_not_spin_on_tty_eof(monkeypatch):
    import termios, tty

    class Spin(Exception):
        pass

    class FakeTTY:
        def isatty(self): return True
        def fileno(self): return 0

    n = [0]

    def fake_read(fd, k):
        n[0] += 1
        if n[0] > 500:
            raise Spin
        return b''

    monkeypatch.setattr(sys, 'stdin', FakeTTY())
    monkeypatch.setattr(termios, 'tcgetattr', lambda fd: [])
    monkeypatch.setattr(termios, 'tcsetattr', lambda *a: None)
    monkeypatch.setattr(tty, 'setcbreak', lambda fd: None)
    monkeypatch.setattr(lazy_typer.os, 'read', fake_read)
    try:
        lazy_typer.arrow_key_select(['Update Now', 'Continue'])
    except Spin:
        pytest.fail('arrow_key_select busy-loops forever when the terminal hits EOF')
    except Exception:
        pass
