import numpy as np
from app.schemas.candle import Candle, available
from app.config import ENGINE_CONFIG, INTERVAL_MS


def volatility(candles: list[Candle], cutoff_timestamp: int, timeframe: str, atr: float) -> dict:
    bars = available(candles, cutoff_timestamp)
    prices = np.array([c.close for c in bars[-ENGINE_CONFIG['hv_window']-1:]])
    hv = np.std(np.diff(np.log(prices)), ddof=1) * np.sqrt(365*86400000/INTERVAL_MS[timeframe])*100
    pct = atr/bars[-1].close*100
    return {'atr14': atr, 'atr_percent': pct, 'historical_volatility_annualized_pct': float(hv),
            'hv_window': ENGINE_CONFIG['hv_window'], 'classification': ['low','normal','high','extreme'][sum(pct >= b for b in ENGINE_CONFIG['volatility_atr_bands'])]}
