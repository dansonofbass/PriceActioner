export type Intent = { action: string; action_timing_days: number; holding_period_days: number | null; risk_profile: string; priority: string; owns_btc: boolean; entry_price: number | null };
export type Candle = { timestamp: number; close_timestamp: number; open: number; high: number; low: number; close: number; volume: number; closed: boolean };
export type Market = { candles: Candle[]; fetched_at: number; timeframe: string; status: string };
export type Zone = { low: number; high: number; midpoint: number; strength: number; touches: number; major: boolean; zone_type: string; breakdown: Record<string, number> };
export type Plan = { requested_horizon_days: number; primary_timeframe: string; secondary_timeframe: string; context_timeframe: string; timeframe_weights: Record<string, number> };
export type Context = {
 current_price: number; user_intent: Intent; analysis_plan: Plan; generated_at: string;
 market_structures: Record<string, { state: string; sequence: { label: string | null; price: number }[] }>;
 support_resistance: Record<string, { nearest_support: Zone | null; nearest_resistance: Zone | null }>;
 momentum: Record<string, { rsi14: number; ema20: number; ema50: number; ema200: number; macd: number; macd_histogram: number; ema20_slope: string }>;
 volume: Record<string, { volume_ratio: number | null; taker_buy_ratio: number | null; classification: string }>;
 volatility: Record<string, { atr14: number; atr_percent: number; historical_volatility_annualized_pct: number; classification: string }>;
 price_action: Record<string, { events: { event: string; level: number }[]; volume_confirmed: boolean }>;
 deterministic_evidence: { bullish_evidence: number; bearish_evidence: number; uncertain: number; breakdown: Record<string, { weight: number; signal: number; bullish: number; bearish: number; uncertain: number }> };
 thesis_invalidation: { current_structure_valid_while: string; weakening_conditions: string[]; strong_invalidation: { condition: string; level: number | null; structure_condition: string } | null };
};
export type Usage = { limit: number; used: number; remaining: number; resets_at: string; scope: string; timezone: string };
export type Result = { analysis_id: string; timestamp: string; context: Context; alignment: { alignment_score: number; alignment_direction: string }; status: string; missing_timeframes: string[]; engine_version: string; jev_mode: string; price_basis: string; usage?: Usage; human_preview?: string; request_preview?: { payload: { model: string | null; state: Context; questions: Record<string,unknown>[] }; serialized_request: string; character_count: number; approximate_token_count: number; schema_status: string } };
