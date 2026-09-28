import numpy as np
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD
from ta.volatility import AverageTrueRange
from app.schemas.candle import Candle, available
from app.config import ENGINE_CONFIG


def atr_value(candles: list[Candle], cutoff_timestamp: int) -> float:
    bars = available(candles, cutoff_timestamp)
    period = ENGINE_CONFIG['indicator_period']
    if len(bars) < period: raise ValueError('Insufficient ATR samples')
    return float(AverageTrueRange(pd.Series([c.high for c in bars]), pd.Series([c.low for c in bars]),
                                 pd.Series([c.close for c in bars]), window=period).average_true_range().iloc[-1])


def indicators(candles: list[Candle], cutoff_timestamp: int) -> dict:
    bars = available(candles, cutoff_timestamp)
    if len(bars) < ENGINE_CONFIG['minimum_candles']:
        raise ValueError('At least 205 closed candles required for EMA200 and slope')
    close = pd.Series([c.close for c in bars], dtype=float)
    periods = ENGINE_CONFIG['macd_periods']
    macd = MACD(close, window_slow=periods['slow'], window_fast=periods['fast'], window_sign=periods['signal'])
    atr = atr_value(bars,cutoff_timestamp)
    result = {'rsi14': float(RSIIndicator(close, window=ENGINE_CONFIG['indicator_period']).rsi().iloc[-1]),
              'macd': float(macd.macd().iloc[-1]), 'macd_signal': float(macd.macd_signal().iloc[-1]),
              'macd_histogram': float(macd.macd_diff().iloc[-1]), 'atr14': float(atr),
              'atr_percent': float(atr / close.iloc[-1] * 100),
              'input_candles_count': len(bars), 'valid_calculation_sample_size': len(bars) - 199,
              'latest_candle_time': bars[-1].close_timestamp}
    for period in ENGINE_CONFIG['ema_periods']:
        ema = EMAIndicator(close, window=period).ema_indicator()
        value = float(ema.iloc[-1])
        slope = float((value / ema.iloc[-1-ENGINE_CONFIG['ema_slope_bars']] - 1) * 100)
        result.update({f'ema{period}': value, f'ema{period}_distance_pct': float((close.iloc[-1]/value-1)*100),
                       f'ema{period}_slope_pct': slope, f'ema{period}_slope': 'rising' if slope > 0 else 'falling' if slope < 0 else 'flat'})
    return {key: None if isinstance(value, float) and not np.isfinite(value) else value for key, value in result.items()}
