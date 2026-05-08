from typing import Literal, Optional

from pydantic import BaseModel

AnalysisMode = Literal["quick", "deep"]
DefaultMarket = Literal["KR", "US"]
HorizonType = Literal["intraday", "swing", "long_term"]


class Settings(BaseModel):
    analysis_mode: AnalysisMode = "quick"
    default_market: DefaultMarket = "KR"
    default_horizon: Optional[HorizonType] = None


class SettingsUpdate(BaseModel):
    analysis_mode: Optional[AnalysisMode] = None
    default_market: Optional[DefaultMarket] = None
    default_horizon: Optional[HorizonType] = None
