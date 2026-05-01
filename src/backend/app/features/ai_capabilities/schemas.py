from typing import Dict, List, Literal, Optional

from pydantic import BaseModel

CapabilityLevel = Literal["supported", "degraded", "unsupported"]


class CapabilityStatus(BaseModel):
    level: CapabilityLevel
    reason: Optional[str] = None


class PromptInventoryItem(BaseModel):
    key: str
    version: str
    owner_feature: str
    purpose: str


class AiCapabilitiesResponse(BaseModel):
    providers: Dict[str, Dict[str, CapabilityStatus]]
    prompt_inventory: List[PromptInventoryItem]

