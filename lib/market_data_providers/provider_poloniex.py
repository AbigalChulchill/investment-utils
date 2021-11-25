from datetime import datetime
from .interface import MarketDataProvider
from lib.common.id_map_poloniex import id_to_poloniex
from lib.trader.poloniex_api import Poloniex as PoloniexAPI
import pandas as pd
import datetime


class MarketDataProviderPoloniex(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return asset in id_to_poloniex.keys()

    def __init__(self):
        self._api= PoloniexAPI("","")

    def get_market_price(self, asset: str) -> float:
        return self._api.returnTicker(id_to_poloniex[asset])

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
        ts_end = datetime.datetime.now().timestamp()
        ts_start = ts_end - days_before * 24 * 3600
        candles = self._api.returnChartData(id_to_poloniex[asset], "1d", ts_start, ts_end)
        df = pd.DataFrame.from_dict(candles)
        #df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
        df.rename(columns={ "date": "timestamp"}, inplace=True)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="s"))
        df.set_index('timestamp', inplace=True)
        return df
