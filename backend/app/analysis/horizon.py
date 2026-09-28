from app.config import ENGINE_CONFIG
from app.schemas.intent import AnalysisPlan, UserIntent


def plan_for(intent: UserIntent) -> AnalysisPlan:
    days = intent.holding_period_days or max(1, intent.action_timing_days)
    weights = next(row['weights'] for row in ENGINE_CONFIG['horizon_weights'] if days <= row['max_days'])
    ranked = sorted(weights, key=weights.get, reverse=True)
    return AnalysisPlan(requested_horizon_days=days, primary_timeframe=ranked[0], secondary_timeframe=ranked[1], context_timeframe=ranked[2], timeframe_weights=weights)
