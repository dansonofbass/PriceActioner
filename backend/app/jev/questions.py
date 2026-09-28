# Local inspection schema only. No claim of compatibility with a live TypeSafe API.
QUESTIONS = [
    {'id':'direction','type':'choice','options':['strong_bearish','bearish','neutral','bullish','strong_bullish'],'instruction':"Given the supplied deterministic BTC/USDT market state and the user's requested holding horizon, which directional market regime is most consistent with the evidence?"},
    {'id':'horizon_fit','type':'choice','options':['poor_fit','weak_fit','reasonable_fit','strong_fit','uncertain'],'instruction':"How well does the current market structure support maintaining the leading directional thesis across the user's requested holding horizon?"},
    {'id':'trend_persistence','type':'choice','options':['less_than_24h','one_to_three_days','four_to_seven_days','one_to_two_weeks','longer','uncertain'],'instruction':'Considering the supplied multi-timeframe structure, support/resistance, momentum, volume and volatility evidence, which persistence window is most consistent with the current regime?'},
    {'id':'evidence_quality','type':'choice','options':['weak','mixed','moderate','strong','very_strong'],'instruction':'Assess the quality of the supplied deterministic evidence.'},
    {'id':'risk','type':'score','instruction':"Evaluate market risk for the user's stated action and holding horizon using only the supplied market state."},
    {'id':'supports_user_plan','type':'noul','instruction':"Does the supplied market evidence support the user's stated action and requested holding horizon?"},
]
