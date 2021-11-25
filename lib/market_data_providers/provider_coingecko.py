from .interface import MarketDataProvider
from ..common.misc import is_stock

import pycoingecko
import pandas as pd

class MarketDataProviderCoingecko(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return not is_stock(asset)

    def __init__(self):
        self._cg = pycoingecko.CoinGeckoAPI()

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
