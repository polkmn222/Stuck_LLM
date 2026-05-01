from app.features.conversations.formatting import (
    conversation_summary,
    detect_language,
    format_horizon,
)


def test_conversation_formatting_helpers_preserve_summary_and_language_behavior() -> None:
    stored = {
        "status": "analysis_completed",
        "messages": [
            {
                "id": "msg_user",
                "role": "user",
                "content": "애플 예측을 장기 관점으로 다시 정리해줘",
                "meta": "submitted",
                "created_at": "2026-04-29T00:00:00Z",
            },
            {
                "id": "msg_assistant",
                "role": "assistant",
                "content": "장기 관점 요약입니다.",
                "meta": "analysis completed",
                "created_at": "2026-04-29T00:00:01Z",
            },
        ],
    }

    summary = conversation_summary("conv_phase098", stored)

    assert detect_language("애플 전망") == "ko"
    assert format_horizon("swing", "ko") == "스윙"
    assert summary.conversation_id == "conv_phase098"
    assert summary.status == "analysis_completed"
    assert summary.title == "애플 예측을 장기 관점으로 다시 정리해줘"
    assert summary.last_message == "장기 관점 요약입니다."
