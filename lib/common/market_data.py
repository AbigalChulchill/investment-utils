import pycoingecko
import talib
import pandas as pd
import yfinance as yf
from typing import List
from .. trader.binance_api import Binance as BinanceAPI
from .. common.convert import coingecko_id_to_binance



def is_stock(asset: str):
    return asset[0] == "#"


class MarketData:
    def __init__(self, asset_ids: List[str] = None):
        # caching price data for all available coins at once
        # so we don't call API for every single item (because of frequency limits)
        coin_ids = [x for x in asset_ids if not is_stock(x)]
        cg = pycoingecko.CoinGeckoAPI()
        self.price_data = cg.get_price(ids=coin_ids, vs_currencies='usd', include_24hr_change="true")

    def get_market_price(self, asset: str) -> float:
        if is_stock(asset):
            ticker = yf.Ticker(asset.replace("#", ""))
            return ticker.info['currentPrice']
        else:
            return float(self.price_data[asset]['usd'])

    def get_24h_change(self, asset: str) -> float:
        if is_stock(asset):
            return 0
        else:
            return float(self.price_data[asset]['usd_24h_change'])

    def get_avg_price_n_days(self, asset: str, days_before: int) -> float:
        if is_stock(asset):
            ticker = yf.Ticker(asset.replace("#", ""))
            if days_before <= 30:
                period = "1mo"
            elif days_before <= 90:
                period = "3mo"
            elif days_before <= 182:
                period = "6mo"
            elif days_before <= 365:
                period = "1y"
            df = ticker.history(period=period)
            df['ma'] = talib.MA(df['Close'], days_before)
        else:
            api = BinanceAPI()
            candles = api.get_candles_by_limit(coingecko_id_to_binance[asset], "1d", limit=days_before)
            df = pd.DataFrame.from_dict(candles)
            df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
            df.set_index('timestamp', inplace=True)
            df['ma'] = talib.MA(df['close'], days_before)
        r = df['ma'][-1]
        if r != r:
            raise ValueError("ma == NaN")
        return r
