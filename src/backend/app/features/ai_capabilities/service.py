from app.features.ai_capabilities.schemas import (
    AiCapabilitiesResponse,
    CapabilityStatus,
    PromptInventoryItem,
)


def get_ai_capabilities() -> AiCapabilitiesResponse:
    return AiCapabilitiesResponse(
        providers={
            "openai": {
                "chat_completion": CapabilityStatus(level="supported"),
                "intent_routing": CapabilityStatus(level="supported"),
                "stock_analysis": CapabilityStatus(level="supported"),
                "news_summary": CapabilityStatus(level="supported"),
                "prediction_artifact_cache": CapabilityStatus(level="supported"),
            },
            "cerebras": {
                "chat_completion": CapabilityStatus(level="supported"),
                "intent_routing": CapabilityStatus(level="supported"),
                "stock_analysis": CapabilityStatus(level="supported"),
                "news_summary": CapabilityStatus(level="supported"),
                "prediction_artifact_cache": CapabilityStatus(level="supported"),
            },
            "custom_openai_compatible": {
                "chat_completion": CapabilityStatus(level="supported"),
                "intent_routing": CapabilityStatus(level="degraded", reason="model-dependent JSON quality"),
                "stock_analysis": CapabilityStatus(level="degraded", reason="model-dependent JSON quality"),
                "news_summary": CapabilityStatus(level="degraded", reason="model-dependent JSON quality"),
                "prediction_artifact_cache": CapabilityStatus(level="supported"),
            },
            "local_model": {
                "chat_completion": CapabilityStatus(level="degraded", reason="not wired by default"),
                "intent_routing": CapabilityStatus(level="unsupported", reason="no local runtime adapter"),
                "stock_analysis": CapabilityStatus(level="unsupported", reason="no local runtime adapter"),
                "news_summary": CapabilityStatus(level="unsupported", reason="no local runtime adapter"),
                "prediction_artifact_cache": CapabilityStatus(level="supported"),
            },
        },
        prompt_inventory=[
            PromptInventoryItem(
                key="chat_completion",
                version="phase_026_chat_completion_v1",
                owner_feature="conversations",
                purpose="General assistant replies with recent conversation context.",
            ),
            PromptInventoryItem(
                key="chat_intent",
                version="phase_026_chat_intent_v1",
                owner_feature="conversations",
                purpose="Structured intent routing for stock, news, chart, and chat requests.",
            ),
            PromptInventoryItem(
                key="live_stock_analysis",
                version="phase_095_live_analysis_v1",
                owner_feature="analysis",
                purpose="Source-grounded analysis over eligible evidence before scoring.",
            ),
            PromptInventoryItem(
                key="news_digest_summary",
                version="phase_074_news_digest_summary_v1",
                owner_feature="conversations",
                purpose="Compact Korean or English summary from linked news metadata only.",
            ),
            PromptInventoryItem(
                key="prediction_artifact",
                version="phase_095_v1",
                owner_feature="processing_cache",
                purpose="Cacheable prediction output keyed by evidence, prompt, provider, and model.",
            ),
        ],
    )

