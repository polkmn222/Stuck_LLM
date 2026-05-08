from typing import Dict, List, Literal, Optional

from pydantic import BaseModel, Field, SecretStr, field_validator, model_validator

CredentialProvider = Literal["openai", "anthropic", "cerebras", "custom"]
ExternalCredentialProvider = Literal["tavily", "gnews", "serpapi", "eventregistry"]
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
    credential_id: Optional[str] = Field(default=None, min_length=1, max_length=80)
    label: Optional[str] = Field(default=None, max_length=120)
    provider: CredentialProvider
    model: str = Field(min_length=1, max_length=120)
    base_url: Optional[str] = Field(default=None, max_length=500)
    api_key: SecretStr = Field(min_length=1, max_length=4000)
    make_active: bool = True

    @field_validator("credential_id", "label", "model", "base_url", mode="before")
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
    credential_id: Optional[str] = None
    label: Optional[str] = None
    provider: Optional[CredentialProvider] = None
    model: Optional[str] = None
    base_url: Optional[str] = None
    api_key_mask: Optional[str] = None
    key_source: Optional[str] = None
    is_active: bool = False
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
    credential_id: str
    label: Optional[str] = None
    provider: CredentialProvider
    model: str
    base_url: str
    api_key: str


class LlmCredentialListResponse(BaseModel):
    active_credential_id: Optional[str]
    credentials: List[LlmCredentialStatus]


class ExternalCredentialUpsert(BaseModel):
    credential_id: Optional[str] = Field(default=None, min_length=1, max_length=80)
    label: Optional[str] = Field(default=None, max_length=120)
    provider: ExternalCredentialProvider
    api_key: SecretStr = Field(min_length=1, max_length=4000)
    make_active: bool = True

    @field_validator("credential_id", "label", mode="before")
    @classmethod
    def strip_optional_text(cls, value: object) -> object:
        if isinstance(value, str):
            stripped = value.strip()
            return stripped or None
        return value


class ExternalCredentialStatus(BaseModel):
    configured: bool
    credential_id: Optional[str] = None
    label: Optional[str] = None
    provider: Optional[ExternalCredentialProvider] = None
    api_key_mask: Optional[str] = None
    key_source: Optional[str] = None
    is_active: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ExternalCredentialSecret(BaseModel):
    credential_id: str
    label: Optional[str] = None
    provider: ExternalCredentialProvider
    api_key: str


class ExternalCredentialListResponse(BaseModel):
    active_credential_ids: Dict[ExternalCredentialProvider, str]
    credentials: List[ExternalCredentialStatus]
