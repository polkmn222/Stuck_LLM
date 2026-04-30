from typing import Literal, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

CredentialProvider = Literal["openai", "anthropic", "cerebras", "custom"]
LlmConnectionTestStatus = Literal["ok", "setup_needed", "provider_error"]

CEREBRAS_DEFAULT_MODEL = "llama3.1-8b"
CEREBRAS_COMPARISON_MODELS = [
    CEREBRAS_DEFAULT_MODEL,
    "qwen-3-235b-a22b-instruct-2507",
]

DEFAULT_BASE_URLS = {
    "openai": "https://api.openai.com/v1",
    "anthropic": "https://api.anthropic.com/v1",
    "cerebras": "https://api.cerebras.ai/v1",
}


class LlmCredentialUpsert(BaseModel):
    provider: CredentialProvider
    model: str = Field(min_length=1, max_length=120)
    base_url: Optional[str] = Field(default=None, max_length=500)
    api_key: SecretStr = Field(min_length=1, max_length=4000)

    @field_validator("model", "base_url", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value

    @model_validator(mode="after")
    def require_provider_base_url(self) -> "LlmCredentialUpsert":
        if self.provider == "custom" and not self.base_url:
            raise ValueError("custom provider requires base_url")
        if self.base_url is None:
            self.base_url = DEFAULT_BASE_URLS.get(self.provider)
        return self


class LlmCredentialStatus(BaseModel):
    configured: bool
    provider: Optional[CredentialProvider] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key_mask: Optional[str] = None
    key_source: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class LlmConnectionTestResult(BaseModel):
    configured: bool
    status: LlmConnectionTestStatus
    provider: Optional[CredentialProvider] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    key_source: Optional[str] = None
    error_code: Optional[str] = None
    message: str


class LlmCredentialSecret(BaseModel):
    provider: CredentialProvider
    model: str
    base_url: str
    api_key: str
