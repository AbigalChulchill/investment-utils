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
        pass

    def get_market_price(self, asset: str) -> float:
        return self.get_historical_bars(asset, 1, True)['close'].iat[-1]

    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool =False)->pd.DataFrame:
        ts_end = datetime.datetime.now().timestamp()
        ts_start = ts_end - days_before * 24 * 3600
        candles = PoloniexAPI("","").returnChartData(id_to_poloniex[asset], "1d", ts_start, ts_end)
        df = pd.DataFrame.from_dict(candles)
        if not with_partial_today_bar:
            df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
        df.rename(columns={ "date": "timestamp"}, inplace=True)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
        df.set_index('timestamp', inplace=True)
        return df
