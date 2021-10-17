import talib
#import pandas as pd
import numpy as np
from typing import List
from .. market_data_providers.flyweight import MarketDataProviderFlyweight


class MarketData:
    def __init__(self, asset_ids: List[str] = None):
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


    def get_avg_price_n_days(self, asset: str, days_before: int) -> float:
        df = self._provider_flyweight.get(asset).get_historical_bars(asset, days_before)
        if len(df) > 0:
            ma_type = talib.SMA if days_before > 10 else talib.EMA
            df['ma'] = ma_type(df['close'], min(len(df), days_before))
            r = df['ma'][-1]
            if r != r:
                raise ValueError("ma == NaN")
            return r
        return self.get_market_price(asset)

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        avg = self.get_avg_price_n_days(coin, days_before)
        current = self.get_market_price(coin)
        return (current - avg) / current * 100.
