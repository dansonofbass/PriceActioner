from pydantic import BaseModel, ConfigDict, Field, model_validator


class Candle(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    timestamp: int
    close_timestamp: int
    open: float = Field(gt=0)
    high: float = Field(gt=0)
    low: float = Field(gt=0)
    close: float = Field(gt=0)
    volume: float = Field(ge=0)
    quote_volume: float = Field(ge=0)
    trades: int = Field(ge=0)
    taker_buy_base_volume: float = Field(ge=0)
    taker_buy_quote_volume: float = Field(ge=0)
    closed: bool

    @model_validator(mode='after')
    def coherent(self):
        if not self.low <= min(self.open, self.close) <= max(self.open, self.close) <= self.high:
            raise ValueError('Invalid OHLC bounds')
        if self.close_timestamp < self.timestamp or self.taker_buy_base_volume > self.volume + 1e-8:
            raise ValueError('Invalid candle time or taker volume')
        return self


def available(candles: list[Candle], cutoff_timestamp: int) -> list[Candle]:
    """Single time boundary used by every candle-based calculation. UTC milliseconds."""
    return sorted((c for c in candles if c.closed and c.close_timestamp <= cutoff_timestamp), key=lambda c: c.timestamp)
