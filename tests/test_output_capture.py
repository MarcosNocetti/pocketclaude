import pytest
from unittest.mock import patch, MagicMock
import output_capture


def test_strip_ansi_removes_color_codes():
    colored = "\x1B[32mHello\x1B[0m World"
    assert output_capture.strip_ansi(colored) == "Hello World"


def test_strip_ansi_leaves_plain_text():
    plain = "Hello World"
    assert output_capture.strip_ansi(plain) == "Hello World"


def test_compute_delta_returns_new_lines():
    before = "linha1\nlinha2\nlinha3"
    after = "linha1\nlinha2\nlinha3\nlinha4\nlinha5"
    delta = output_capture.compute_delta(before, after)
    assert "linha4" in delta
    assert "linha5" in delta


def test_compute_delta_empty_before():
    before = ""
    after = "saida do comando"
    assert output_capture.compute_delta(before, after) == "saida do comando"


def test_compute_delta_no_new_content():
    content = "linha1\nlinha2"
    assert output_capture.compute_delta(content, content) == ""


def test_capture_pane_calls_tmux():
    mock_result = MagicMock()
    mock_result.stdout = "output da sessao\n"
    with patch("subprocess.run", return_value=mock_result) as mock_run:
        result = output_capture.capture_pane("minha-sessao")
    mock_run.assert_called_once_with(
        ["tmux", "capture-pane", "-p", "-t", "minha-sessao"],
        capture_output=True, text=True
    )
    assert result == "output da sessao\n"
