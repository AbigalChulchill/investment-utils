from typing import List
from math import nan
from .interface import MarketDataProvider
from lib.common.id_ticker_map import id_to_ticker
from lib.common.misc import is_stock

import pycoingecko
import pandas as pd

class MarketDataProviderCoingecko(MarketDataProvider):
    def __init__(self):
        self._cg = pycoingecko.CoinGeckoAPI()
        market_cap_list = self._cg.get_coins_markets(ids=list(id_to_ticker.keys()), vs_currency="usd")
        self._cached = {}
        for entry in market_cap_list:
            self._cached [entry['id']] = entry

    def get_supported_methods(self, asset: str) -> List[str]:
        if not is_stock(asset):
            return [
                "get_market_price",
                "get_historical_bars",
                "get_market_cap",
                "get_max_supply",
            ]
        else:
            return []


    def get_market_price(self, asset: str) -> float:
        price_data = self._cg.get_price(ids=[asset], vs_currencies="usd", include_24hr_change="false")
        return float(price_data[asset]['usd'])

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
        cg_candles = self._cg.get_coin_ohlc_by_id(asset, "usd", 30)
        candles =[]
        current_ic = 0
        last_ic = len(cg_candles)
        while current_ic < last_ic:
            eod_ic = min(last_ic-1, current_ic+5)
            # collapse 6 4h candles into one 1d candle
            first_candle = cg_candles[current_ic]
            last_candle = cg_candles[eod_ic]
            candles_day = cg_candles[current_ic:(eod_ic+1)]
            highest_day = max([x[2] for x in candles_day])
            lowest_day = min([x[3] for x in candles_day])
            candles.append(
                {
                    'timestamp': first_candle[0],
                    'open': first_candle[1],
                    'high': highest_day,
                    'low': lowest_day,
                    'close': last_candle[4],
                })
            current_ic += 6

        df = pd.DataFrame.from_dict(candles)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
        df.set_index('timestamp', inplace=True)
        return df

    def get_market_cap(self, asset: str) -> int:
        return self._cached[asset]['market_cap'] if 'market_cap' in self._cached[asset] and self._cached[asset]['market_cap'] is not None else nan

    def get_max_supply(self, asset: str) -> int:
        return self._cached[asset]['max_supply'] if 'max_supply' in self._cached[asset] and self._cached[asset]['max_supply'] is not None  else nan
