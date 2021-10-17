from .interface import MarketDataProvider
from lib.common.id_map_binance import id_to_binance
from lib.trader.binance_api import Binance as BinanceAPI
import pandas as pd


class MarketDataProviderBinance(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return asset in id_to_binance.keys()

    def __init__(self):
        self._crypto_prices = BinanceAPI().get_prices()

    def get_market_price(self, asset: str) -> float:
        return float([x['price'] for x in self._crypto_prices if x['symbol'] == id_to_binance[asset]][0])

    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool =False)->pd.DataFrame:
        candles = BinanceAPI().get_candles_by_limit(id_to_binance[asset], "1d", limit=days_before)
        df = pd.DataFrame.from_dict(candles)
        if not with_partial_today_bar:
            df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
        df.set_index('timestamp', inplace=True)
        return df
