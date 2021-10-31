import talib
import numpy as np
from typing import List
from .. market_data_providers.flyweight import MarketDataProviderFlyweight
from lib.common.msg import warn


class MarketData:
    def __init__(self):
        self._provider_flyweight = MarketDataProviderFlyweight()

    def get_market_price(self, asset: str) -> float:
        return self._provider_flyweight.get(asset).get_market_price(asset)

    def is_tradeable(self, asset: str) -> bool:
        return True

    def get_daily_change(self, asset: str) -> float:
        daily_change = 0
        df = self._provider_flyweight.get(asset).get_historical_bars(asset, 2, with_partial_today_bar=True)
        if df.size > 0:
            c = df['close'].to_numpy(dtype=np.double)
            previous_close = c[-2]
            current_price = c[-1]
            daily_change = (current_price - previous_close) / current_price * 100
        return daily_change

    def get_avg_price_n_days(self, asset: str, days_before: int, ma_type: str="auto") -> float:
        df = self._provider_flyweight.get(asset).get_historical_bars(asset, days_before, with_partial_today_bar=True)
        if df.size > 0:
            if ma_type == "auto":
                ta_ma_type = talib.SMA if days_before > 10 else talib.EMA
            elif ma_type == "EMA":
                ta_ma_type = talib.EMA
            else:
                ta_ma_type = talib.SMA
            df['ma'] = ta_ma_type(df['close'], min(len(df), days_before))
            r = df['ma'].to_numpy(dtype=np.double)[-1]
            if r != r:
                raise ValueError("r == NaN")
            return r
        return self.get_market_price(asset)

    def get_rsi(self, asset: str) -> float:
        rsi_period = 14
        df = self._provider_flyweight.get(asset).get_historical_bars(asset, rsi_period + 1, with_partial_today_bar=True)
        r = None
        if df.size >= rsi_period:
            s_rsi = talib.RSI(df['close'], rsi_period)
            r = s_rsi.iat[-1]
            if r != r:
                r = None
        if r is None:
            warn(f"get_rsi ({asset}) failed")
        return r

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        avg = self.get_avg_price_n_days(coin, days_before)
        current = self.get_market_price(coin)
        distance = (current - avg) / avg * 100.
        return distance

    def get_fundamentals(self, asset: str) -> dict:
        return self._provider_flyweight.get(asset).get_fundamentals(asset)
