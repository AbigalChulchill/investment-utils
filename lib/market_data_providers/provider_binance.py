from typing import Tuple
from .interface import MarketDataProvider
from lib.common.id_map_binance import id_to_binance
from lib.trader.binance_api import Binance as BinanceAPI
import pandas as pd

def id_to_ticker(id: str) -> Tuple[str, bool]:
    binance_id = id_to_binance[id]
    reverse = "_r" in binance_id
    ticker = binance_id.replace("_r","") if reverse else binance_id
    return ticker, reverse


class MarketDataProviderBinance(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return asset in id_to_binance.keys()

    def __init__(self):
        self._crypto_prices = BinanceAPI().get_prices()

    def get_market_price(self, asset: str) -> float:
        ticker, reverse = id_to_ticker(asset)
        price = float([x['price'] for x in self._crypto_prices if x['symbol'] == ticker][0])
        return 1 / price if reverse else price

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
        ticker, reverse = id_to_ticker(asset)
        candles = BinanceAPI().get_candles_by_limit(ticker, "1d", limit=days_before)
        df = pd.DataFrame.from_dict(candles)
        df['open'] = pd.to_numeric(df['open'])
        df['close'] =pd.to_numeric(df['close'])
        df['high'] = pd.to_numeric(df['high'])
        df['low'] = pd.to_numeric(df['low'])
        #df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
        df.set_index('timestamp', inplace=True)
        if reverse:
            for n in "open","close","low","high":
                df[n] = 1/df[n]
        return df
