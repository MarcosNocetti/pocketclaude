import json

import queue_manager


def test_is_rate_limited_detects_legacy_usage_message():
    response = "Claude: You're out of extra usage. Please wait until it resets 11:30pm."
    assert queue_manager.is_rate_limited(response) is True


def test_is_rate_limited_detects_token_or_credit_variants():
    assert queue_manager.is_rate_limited("Error: credit balance is too low") is True
    assert queue_manager.is_rate_limited("Error: insufficient tokens, try again at 7:15pm") is True
    assert queue_manager.is_rate_limited("❌ You've hit your limit · resets 3am (America/Sao_Paulo)") is True


def test_parse_reset_time_supports_try_again_format():
    reset_at = queue_manager.parse_reset_time("insufficient tokens, try again at 7:15pm")

    assert reset_at is not None
    assert reset_at.hour == 19
    assert reset_at.minute == 15


def test_enqueue_persists_message(tmp_path, monkeypatch):
    queue_file = tmp_path / "queue.json"
    monkeypatch.setattr(queue_manager, "QUEUE_FILE", str(queue_file))

    count = queue_manager.enqueue(
        chat_id=123,
        session_name="main",
        cwd="/tmp",
        claude_id="abc",
        text="hello",
        reset_at=None,
    )

    assert count == 1
    assert json.loads(queue_file.read_text())[0]["text"] == "hello"
