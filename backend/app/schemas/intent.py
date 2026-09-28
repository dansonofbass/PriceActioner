from typing import Literal
from pydantic import BaseModel, Field, ConfigDict, model_validator


class UserIntent(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    action: Literal['buy', 'sell', 'hold', 'wait']
    action_timing_days: float = Field(ge=0, le=30)
    holding_period_days: float | None = Field(default=None, ge=1, le=30)
    risk_profile: Literal['conservative', 'balanced', 'aggressive']
    priority: Literal['avoid_bad_entry', 'catch_trend_early', 'balanced']
    owns_btc: bool = False
    entry_price: float | None = Field(default=None, gt=0)

    @model_validator(mode='after')
    def valid_entry(self):
        if self.entry_price is not None and not self.owns_btc:
            raise ValueError('Entry price requires owns_btc')
        if self.action == 'hold' and not self.owns_btc:
            raise ValueError('Already own BTC requires owns_btc')
        return self


class AnalysisPlan(BaseModel):
    requested_horizon_days: float
    primary_timeframe: str
    secondary_timeframe: str
    context_timeframe: str
    timeframe_weights: dict[str, float]
