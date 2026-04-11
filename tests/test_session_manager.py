import pytest
from unittest.mock import patch, MagicMock, call
import session_manager


def make_run(returncode=0, stdout=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    return m


def test_get_active_starts_as_none():
    session_manager._active_session = None
    assert session_manager.get_active() is None


def test_set_active_and_get():
    session_manager.set_active("minha-sessao")
    assert session_manager.get_active() == "minha-sessao"
    session_manager.set_active(None)


def test_session_exists_true():
    with patch("subprocess.run", return_value=make_run(0)):
        assert session_manager.session_exists("existe") is True


def test_session_exists_false():
    with patch("subprocess.run", return_value=make_run(1)):
        assert session_manager.session_exists("nao-existe") is False


def test_new_session_creates_and_activates():
    def side_effect(cmd, **kwargs):
        if "has-session" in cmd:
            return make_run(1)  # não existe ainda
        return make_run(0)  # new-session ok

    with patch("subprocess.run", side_effect=side_effect):
        result = session_manager.new_session("nova")
    assert result is True
    assert session_manager.get_active() == "nova"
    session_manager.set_active(None)


def test_new_session_fails_if_exists():
    with patch("subprocess.run", return_value=make_run(0)):  # has-session ok
        result = session_manager.new_session("existente")
    assert result is False


def test_attach_session_sets_active():
    with patch("subprocess.run", return_value=make_run(0)):
        result = session_manager.attach_session("minha")
    assert result is True
    assert session_manager.get_active() == "minha"
    session_manager.set_active(None)


def test_attach_session_fails_if_not_found():
    with patch("subprocess.run", return_value=make_run(1)):
        result = session_manager.attach_session("fantasma")
    assert result is False


def test_kill_session_clears_active_if_was_active():
    session_manager.set_active("alvo")

    def side_effect(cmd, **kwargs):
        if "has-session" in cmd:
            return make_run(0)
        return make_run(0)

    with patch("subprocess.run", side_effect=side_effect):
        result = session_manager.kill_session("alvo")
    assert result is True
    assert session_manager.get_active() is None


def test_kill_session_preserves_other_active():
    session_manager.set_active("outra")

    def side_effect(cmd, **kwargs):
        if "has-session" in cmd:
            return make_run(0)
        return make_run(0)

    with patch("subprocess.run", side_effect=side_effect):
        session_manager.kill_session("alvo")
    assert session_manager.get_active() == "outra"
    session_manager.set_active(None)


def test_list_sessions_parses_output():
    with patch("subprocess.run", return_value=make_run(0, "sessao1\nsessao2\n")):
        sessions = session_manager.list_sessions()
    assert sessions == ["sessao1", "sessao2"]


def test_list_sessions_empty_on_error():
    with patch("subprocess.run", return_value=make_run(1)):
        assert session_manager.list_sessions() == []


def test_send_keys_calls_tmux():
    with patch("subprocess.run", return_value=make_run(0)) as mock_run:
        result = session_manager.send_keys("minha", "git status")
    mock_run.assert_called_once_with(
        ["tmux", "send-keys", "-t", "minha", "git status", "Enter"],
        capture_output=True
    )
    assert result is True
