# Deterministic calculation reference

## Input and indicators

Provider: public Binance `/api/v3/klines`, BTCUSDT, intervals 15m/1h/4h/1d (500 rows) and 1w (300 rows). Normalization follows the [official Binance market-data schema](https://developers.binance.com/docs/binance-spot-api-docs/rest-api/market-data-endpoints). No signed endpoints are used. The provider validates OHLC, finite positive prices, nonnegative volumes, taker base volume, ordered unique timestamps, gaps, and freshness. UTC milliseconds are retained unchanged.

The `ta` library implements RSI14 (exponentially smoothed gains/losses with alpha 1/14), EMA20/50/200 (alpha 2/(period+1), first close seed), MACD12/26 with a 9-period EMA signal, and Wilder ATR14 (initial mean of 14 true ranges, then `(prior*13 + TR)/14`). Indicator tests independently reconstruct these formulas. EMA slope is percentage change over 5 closed bars. Distance is `(closed_price / EMA - 1) * 100`. At least 205 closed bars are required. EMA200 valid sample count is `n - 199`; other indicators have their own shorter warmups.

Volume ratio is current closed volume divided by the mean of the **previous** 20 candles. Zero denominator gives null. Taker buy is Binance taker buy base / total base; taker sell is its complement. Volume bands are <0.5 very low, <0.8 low, <1.3 normal, <2 high, otherwise very high. All volume is specific to Binance spot.

ATR% is ATR / last closed price × 100. Volatility labels use ATR% bands 1, 3, and 6. Historical volatility is sample standard deviation of 30 log returns × sqrt(365 × bars/day) × 100; it is annualized and depends on the timeframe. This is a descriptive convention, not a forward forecast.

## Zones and events

Confirmed lows propose support; confirmed highs propose resistance. Pivots occurring at both scales are deduplicated and tagged major. Within each type, sorted prices cluster only while max-min <= ATR×0.25 (no unbounded single-link chaining). Zone bounds extend half a tolerance beyond cluster min/max.

- Touch score: min(1, distinct touch episodes / 5) × 25. Consecutive intersecting candles are one episode.
- Recency: max(0, 1 - bars_since_last_touch/100) × 20.
- Rejection: min(1, maximum favorable close displacement / (2×ATR)) × 20.
- Higher timeframe: 25 if an overlapping zone of the same type exists on any higher available timeframe; otherwise 0.
- Volume: min(1, mean touch volume / (trailing-20 mean volume × 1.3)) × 10.

The sum is strength / 100. Absent higher-timeframe data never earns confirmation points. The nearest support must lie fully below reference price; nearest resistance must lie fully above it. An intersected zone may be neither. Missing zones return null, never fabricated levels.

Breakout event zones must be known before the previous candle. Breakouts/breakdowns cross a zone boundary on the current **close**. Failed breakouts reverse a previous close above the zone to a current close below its lower boundary (inverse for failed breakdown). Rejections touch the zone intrabar and close away. Price event and >=1.30 volume confirmation are separate outputs. The initial failed-event rule covers the last two closed candles only; historical multi-bar failure tracking is not claimed.

Classic daily P/R1/S1/R2/S2 use the last completed daily period, never the current open day. Confluence tests ATR×0.5 proximity to EMA20/50/200, major pivots, higher-timeframe overlap and those classic levels. Its strength is factor_count/11 × 100, capped at 100; admin retains factor labels.

## Horizon and evidence

Holding period is the horizon when supplied. Otherwise use max(1, action timing days). Continuous horizon bands are <=1, (1,4], (4,10], (10,20], (20,30]. Highest weight is primary, next is secondary, third is context. Weights are the supplied specification values.

Alignment uses bullish=+1, bearish=-1, range/transition/missing=0. Signed sum is Σ(state×horizon weight). Alignment score is abs(sum)×100; direction is its sign. Missing frames retain their configured weight as uncertainty.

Each evidence component produces a signed signal s in [-1,1]. Bullish points = max(s,0)×weight×100; bearish = max(-s,0)×weight×100; uncertainty = (1-|s|)×weight×100. Components:

| Component | Weight | Signed signal |
|---|---:|---|
| Market structure | 25% | Major state mapping |
| Support/resistance | 20% | (nearest support strength - nearest resistance strength)/100; absent = 0 |
| Breakout/rejection | 15% | Mean event signs; bullish breakout/support rejection/failed breakdown +1, inverse -1, none 0 |
| Alignment | 15% | Signed horizon-weighted sum |
| Volume | 10% | 2×taker buy ratio - 1, missing 0 |
| Momentum | 8% | Mean of RSI's sign relative to 50 and MACD histogram sign |
| Volatility | 7% | Major directional state × max(0,1-ATR%/6) |

Round bullish/bearish to two decimals; uncertain is the residual to 100. These transparent initial rules require empirical evaluation; they do not claim statistical calibration or future returns.

Normalized persistence features reuse the above measurements: alignment magnitude; absolute major state; support strength/100; resistance headroom in ATR units capped at 1 (null if unavailable); absolute momentum signal; volume ratio/1.3 capped at 1; max(0,1-ATR%/6); binary failed events; sum of higher-timeframe weights opposing the primary direction. Missing observations remain visible through the analysis missing-timeframe list and nullable headroom.

Invalidation uses the nearest **major** support below price for bullish structure, or major resistance above price for bearish structure. A confirmed primary close through the outer boundary is strong invalidation; major structure reversal is the other condition. No directional thesis or no major zone produces an explicit unavailable condition rather than an invented price.

## UI libraries

The frontend uses the [Lightweight Charts v5 series API](https://tradingview.github.io/lightweight-charts/docs) with attribution, and [Next.js same-origin rewrites](https://nextjs.org/docs/app/api-reference/config/next-config-js/rewrites). Chart prices can include the current open candle; all deterministic results use closed candles.

