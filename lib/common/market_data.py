import os, talib, json, datetime, pathlib
import pandas as pd
from typing import List, Any
from .. market_data_providers.flyweight import MarketDataProviderFlyweight
from lib.common.msg import warn
from lib.common.misc import calc_raise_percent
from math import nan


class HistoricalBarCache:
    _cache_dir = f"cache/market_data/day_candles/{datetime.datetime.utcnow().strftime('%Y-%m-%d')}"

    def __init__(self):
        self._cache = {}

    @staticmethod
    def _get_cache_file_name(asset: str):
        return f"{HistoricalBarCache._cache_dir}/{asset}.json"

    def put(self, asset: str, df: List[Any]):
        self._cache[asset] = df
        if not os.path.exists(HistoricalBarCache._cache_dir):
            pathlib.Path(HistoricalBarCache._cache_dir).mkdir(parents=True, exist_ok=True)
        cache_file = HistoricalBarCache._get_cache_file_name(asset)
        with open(cache_file, "w") as f:
            d = df.to_dict(orient="records")
            json.dump(d, f)
            
    def get(self, asset: str) -> List[Any]:
        if asset in self._cache.keys():
            return self._cache[asset]
        cache_file = HistoricalBarCache._get_cache_file_name(asset)
        if os.path.exists(cache_file):
            return pd.DataFrame.from_dict(json.load(open(cache_file)))
        else:
            return None

class MarketData:
    def __init__(self):
        self._provider_flyweight = MarketDataProviderFlyweight()
        self._historical_bars_cache = HistoricalBarCache()

    def get_market_price(self, asset: str) -> float:
        return self._provider_flyweight.get(asset, "get_market_price").get_market_price(asset)

    def is_tradeable(self, asset: str) -> bool:
        return True

    def _get_historical_bars(self, asset, days_before):
        max_cache_days = 200
        assert days_before <= max_cache_days
        bar_data = self._historical_bars_cache.get(asset)
        if bar_data is None:
            bar_data = self._provider_flyweight.get(asset, "get_historical_bars").get_historical_bars(asset, max_cache_days)
            self._historical_bars_cache.put(asset, bar_data)
            return bar_data[-days_before-1:]
        else:
            # update close value to current, since cached value is definitely not current
            bar_data['close'].iat[-1] = self.get_market_price(asset)
            # update new low/high if needed
            bar_data['low'].iat[-1] = min(bar_data['low'].iat[-1], bar_data['close'].iat[-1])
            bar_data['high'].iat[-1] = max(bar_data['high'].iat[-1], bar_data['close'].iat[-1])
            return bar_data[-days_before-1:]


    def get_daily_change(self, asset: str) -> float:
        daily_change = 0
        df = self._get_historical_bars(asset, 1)
        if df['close'].size > 1:
            previous_close = df['close'].iat[-2]
            current_price = df['close'].iat[-1]
            daily_change = (current_price - previous_close) / current_price * 100
        return daily_change

    def get_avg_price_n_days(self, asset: str, days_before: int, ma_type: str="auto") -> float:
        df = self._get_historical_bars(asset, days_before)
        if df['close'].size > 1:
            if ma_type == "auto":
                ta_ma_type = talib.SMA if days_before > 10 else talib.EMA
            elif ma_type == "EMA":
                ta_ma_type = talib.EMA
            else:
                ta_ma_type = talib.SMA
            r = ta_ma_type(df['close'], min(df['close'].size-1, days_before)).iat[-1]
            if r != r:
                raise ValueError("r == NaN")
            return r
        return self.get_market_price(asset)

    def get_lo_hi_n_days(self, asset: str, days_before: int) -> float:
        df = self._get_historical_bars(asset, days_before)
        if df['close'].size > 1:
            lo = talib.MIN(df['low'], min(df['close'].size-1, days_before)).iat[-1]
            hi = talib.MAX(df['high'], min(df['close'].size-1, days_before)).iat[-1]
            return lo,hi
        return nan,nan

    def get_rsi(self, asset: str) -> float:
        rsi_period = 14
        df = self._get_historical_bars(asset, rsi_period)
        r = None
        if df['close'].size > rsi_period:
            r = talib.RSI(df['close'], rsi_period).iat[-1]
            if r != r:
                r = None
        return r

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        return calc_raise_percent(self.get_avg_price_n_days(coin, days_before), self.get_market_price(coin))

    def get_fundamentals(self, asset: str) -> dict:
        return self._provider_flyweight.get(asset, "get_fundamentals").get_fundamentals(asset)

    def get_market_cap(self, asset: str) -> int:
        return self._provider_flyweight.get(asset, "get_market_cap").get_market_cap(asset)

    def get_max_supply(self, asset: str) -> int:
        return self._provider_flyweight.get(asset, "get_max_supply").get_max_supply(asset)
