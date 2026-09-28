from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, model_validator
from typing import Literal


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')
    app_env: str = 'development'
    storage_backend: Literal['json', 'redis'] = 'json'
    local_data_dir: str = './data'
    upstash_redis_rest_url: str = ''
    upstash_redis_rest_token: str = ''
    vercel: str = ''
    admin_username: str = 'admin'
    admin_password: str = ''
    admin_secret_key: str = ''
    public_origin: str = 'http://localhost:3000'
    binance_base_url: str = 'https://data-api.binance.vision'
    analysis_engine_version: str = '0.1.0'
    jev_mode: str = 'disabled'
    jev_api_key: str = ''
    jev_model: str = ''
    daily_analysis_limit: int = Field(default=3, ge=1)

    @model_validator(mode='after')
    def guard(self):
        if self.jev_mode != 'disabled':
            raise ValueError('Milestone 1 requires JEV_MODE=disabled; live integration is not implemented.')
        if self.binance_base_url != 'https://data-api.binance.vision':
            raise ValueError('Only the Binance public market-data host is allowed.')
        if self.admin_password and (len(self.admin_password) < 12 or len(self.admin_secret_key) < 32):
            raise ValueError('Use an admin password of at least 12 characters and a secret of at least 32.')
        if self.app_env == 'production' and (not self.admin_secret_key or not self.public_origin.startswith('https://')):
            raise ValueError('Production requires ADMIN_SECRET_KEY and an HTTPS PUBLIC_ORIGIN.')
        if (self.app_env == 'production' or self.vercel) and self.storage_backend != 'redis':
            raise ValueError('Production/Vercel requires STORAGE_BACKEND=redis; local JSON is development-only.')
        if self.upstash_redis_rest_url:
            from urllib.parse import urlsplit
            url = urlsplit(self.upstash_redis_rest_url)
            if url.scheme != 'https' or not url.hostname or not url.hostname.endswith('.upstash.io') or url.username or url.password or url.query or url.fragment or url.path not in ('', '/'):
                raise ValueError('Use the HTTPS REST URL from Upstash, without a path, credentials or query.')
        if self.app_env == 'production' and len(self.admin_secret_key) < 32:
            raise ValueError('Production ADMIN_SECRET_KEY must have at least 32 characters.')
        return self


settings = Settings()
ENGINE_CONFIG = {
    'pivots': {'short': {'left': 5, 'right': 5}, 'major': {'left': 20, 'right': 20}},
    'atr_cluster_multiplier': 0.25,
    'confluence_atr_multiplier': 0.5,
    'volume_threshold': 1.30,
    'volume_bands': [0.5, 0.8, 1.3, 2.0],
    'volatility_atr_bands': [1.0, 3.0, 6.0],
    'zone_weights': {'touch_score': 25, 'recency_score': 20, 'rejection_score': 20, 'higher_tf_score': 25, 'volume_score': 10},
    'zone_touch_cap': 5, 'recency_bars': 100, 'rejection_atr_cap': 2,
    'minimum_candles': 205, 'volume_window': 20, 'hv_window': 30,
    'ema_slope_bars': 5, 'indicator_period': 14,
    'ema_periods': [20, 50, 200], 'macd_periods': {'slow': 26, 'fast': 12, 'signal': 9},
    'rsi_midpoint': 50, 'confluence_factor_cap': 11, 'context_confluence_limit': 6,
    'cache_ttl_ms': 15000, 'freshness_grace_ms': 60000,
    'evidence_weights': {'market_structure': .25, 'support_resistance': .20, 'breakout_rejection': .15, 'alignment': .15, 'volume': .10, 'momentum': .08, 'volatility': .07},
    'state_values': {'bullish': 1, 'bearish': -1, 'range': 0, 'transition': 0},
    'horizon_weights': [
        {'max_days': 1, 'weights': {'15m': .25, '1h': .45, '4h': .30}},
        {'max_days': 4, 'weights': {'1h': .30, '4h': .45, '1d': .25}},
        {'max_days': 10, 'weights': {'1h': .15, '4h': .45, '1d': .40}},
        {'max_days': 20, 'weights': {'4h': .30, '1d': .50, '1w': .20}},
        {'max_days': 30, 'weights': {'4h': .10, '1d': .55, '1w': .35}},
    ],
}
INTERVAL_MS = {'15m': 900000, '1h': 3600000, '4h': 14400000, '1d': 86400000, '1w': 604800000}
