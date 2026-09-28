from datetime import datetime
from pydantic import BaseModel
from .intent import UserIntent, AnalysisPlan


class DecisionContext(BaseModel):
    asset: str = 'BTC/USDT'
    current_price: float
    user_intent: UserIntent
    analysis_plan: AnalysisPlan
    market_structures: dict
    price_action: dict
    support_resistance: dict
    momentum: dict
    volume: dict
    volatility: dict
    confluence: dict
    trend_persistence_features: dict
    deterministic_evidence: dict
    thesis_invalidation: dict
    generated_at: datetime
