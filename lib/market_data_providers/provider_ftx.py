from .interface import MarketDataProvider
from lib.trader.ftx_api import FtxPublic
from lib.common.id_map_ftx import id_to_ftx
import pandas as pd
import datetime

class MarketDataProviderFTX(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return asset in id_to_ftx.keys()

    def __init__(self):
        self._api = FtxPublic()
        self._markets = None

    def _get_market(self, market: str):
        if self._markets is None:
            self._markets = self._api.get_markets()
        market = [m for m in self._markets if m['name'] ==  market][0]
        return market

    def get_market_price(self, asset: str) -> float:
        return self._get_market(id_to_ftx[asset])['price']

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
        t = int(datetime.datetime.now().timestamp())
        seconds_per_day = 3600 * 24
        candles = self._api.get_candles(id_to_ftx[asset], seconds_per_day, t - (seconds_per_day * days_before),  t)
        df = pd.DataFrame.from_dict(candles)
        #df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['startTime']))
        df.set_index('timestamp', inplace=True)
        return df

    def get_fundamentals(self, asset: str) -> dict:
        return {}
