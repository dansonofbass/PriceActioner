def human_preview(c: dict) -> str:
    p=c['analysis_plan']; tf=p['primary_timeframe']; sr=c['support_resistance'][tf]
    lines=['BTC/USDT DECISION CONTEXT',f"User plan: {c['user_intent']['action']} BTC; act in {c['user_intent']['action_timing_days']:g} days; horizon {p['requested_horizon_days']:g} days.",
           f"Risk: {c['user_intent']['risk_profile']}; priority: {c['user_intent']['priority']}",
           f"Primary: {tf}; secondary: {p['secondary_timeframe']}; context: {p['context_timeframe']}"]
    lines += [f"{t}: {s['state']}" for t,s in c['market_structures'].items()]
    for name in ['nearest_support','nearest_resistance']:
        z=sr[name]; lines.append(f"{name}: {z['low']:.2f}–{z['high']:.2f}; strength {z['strength']:.1f}/100" if z else f'{name}: unavailable')
    lines += [f"RSI14: {c['momentum'][tf]['rsi14']:.2f}", f"MACD: {c['momentum'][tf]['macd']:.2f}",
              f"Volume ratio: {c['volume'][tf]['volume_ratio']}", f"Taker buy ratio: {c['volume'][tf]['taker_buy_ratio']}",
              f"ATR: {c['volatility'][tf]['atr_percent']:.2f}%",f"Technical evidence: {c['deterministic_evidence']['bullish_evidence']} bullish / {c['deterministic_evidence']['bearish_evidence']} bearish / {c['deterministic_evidence']['uncertain']} uncertain",
              c['thesis_invalidation']['current_structure_valid_while']]
    return '\n'.join(lines)
