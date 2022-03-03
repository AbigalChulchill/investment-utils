import os, talib, json, datetime, pathlib
import pandas as pd
from typing import List, Tuple, Any, NamedTuple
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

class MarketPriceCache:
    """
        optimizes multiple recent accesses to market price of same asset.  
    """
    class MarketPrice(NamedTuple):
        value:      float
        timestamp:  datetime.datetime

    def __init__(self):
        self._cache = {}

    def put(self, key: str, value: float):
        self._cache[key] = MarketPriceCache.MarketPrice(value=value, timestamp=datetime.datetime.now())

    def get(self, key: str) -> float:
        if key in self._cache:
            # only valid if not older than one minute from now
            if (datetime.datetime.now() - self._cache[key].timestamp) < datetime.timedelta(minutes=1):
                return self._cache[key].value
        return None

class MarketData:
    def __init__(self):
        self._provider_flyweight = MarketDataProviderFlyweight()
        self._historical_bars_cache = HistoricalBarCache()
        self._marketprice_cache = MarketPriceCache()

    def get_market_price(self, asset: str) -> float:
        cached_market_price = self._marketprice_cache.get(asset)
        if cached_market_price is not None:
            return cached_market_price
        else:
            market_price = self._provider_flyweight.get(asset, "get_market_price").get_market_price(asset)
            self._marketprice_cache.put(asset, market_price)
            return market_price

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


    def get_daily_change(self, asset: str) -> Tuple[float,float]:
        daily_change = (0,0)
        daily_change_percent = 0
        df = self._get_historical_bars(asset, 1)
        if df['close'].size > 1:
            previous_close = df['close'].iat[-2]
            current_price = df['close'].iat[-1]
            daily_change = (current_price - previous_close)
            daily_change_percent = (current_price - previous_close) / previous_close * 100
        return daily_change,daily_change_percent

    def get_weekly_change(self, asset: str) -> Tuple[float,float]:
        weekly_change = (0,0)
        weekly_change_percent = 0
        df = self._get_historical_bars(asset, 7)
        if df['close'].size > 1:
            previous_close = df['close'].iat[-8]
            current_price = df['close'].iat[-1]
            weekly_change = (current_price - previous_close)
            weekly_change_percent = (current_price - previous_close) / previous_close * 100
        return weekly_change,weekly_change_percent

    def get_short_term_trend(self, asset: str, length_days: int) -> str:
        df = self._get_historical_bars(asset, length_days)
        c_up = 0
        c_down = 0
        i = -length_days
        while i <= -1:
            if df['open'].iat[i] <= df['close'].iat[i]:
                c_up += 1
            else:
                c_down += 1
            i += 1

        if c_up == length_days:
            return "up"
        elif c_down == length_days:
            return "down"
        else:
            return "side"


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
        df = self._get_historical_bars(asset, 50)
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

    def get_total_supply(self, asset: str) -> int:
        return self._provider_flyweight.get(asset, "get_total_supply").get_total_supply(asset)

    def get_total_volume(self, asset: str) -> int:
        return self._provider_flyweight.get(asset, "get_total_volume").get_total_volume(asset)
