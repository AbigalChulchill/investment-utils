import pycoingecko
import talib
import pandas as pd
import yfinance as yf
import numpy as np
from typing import List
from .. trader.binance_api import Binance as BinanceAPI
from .. common.convert import coingecko_id_to_binance
from .. common.misc import is_stock


class MarketData:
    def __init__(self, asset_ids: List[str] = None):
        # caching price data for all available coins at once
        # so we don't call API for every single item (because of frequency limits)
        coin_ids = [x for x in asset_ids if not is_stock(x)]
        cg = pycoingecko.CoinGeckoAPI()
        self._price_data = cg.get_price(ids=coin_ids, vs_currencies='usd', include_24hr_change="true")
        self._stock_info = dict()

    def _get_cached_stock_info(self, asset: str):
        if not asset in self._stock_info:
            ticker = yf.Ticker(asset.replace("#", ""))
            self._stock_info[asset] = ticker.info
        return self._stock_info[asset]

    def get_market_price(self, asset: str) -> float:
        if is_stock(asset):
            return self._get_cached_stock_info(asset)['currentPrice']
        else:
            return float(self._price_data[asset]['usd'])

    def is_tradeable(self, asset: str) -> bool:
        if is_stock(asset):
            return self._get_cached_stock_info(asset)['tradeable']
        else:
            return True

    def get_daily_change(self, asset: str) -> float:
        daily_change = 0
        df = self._get_historical_bars(asset, 2, with_partial_today_bar=True)
        if df.size > 0:
            c = df['close'].to_numpy(dtype=np.double)
            previous_close = c[-2]
            current_price = c[-1]
            daily_change = (current_price - previous_close) / current_price * 100
        return daily_change


    def _get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool =False)->pd.DataFrame:
        if is_stock(asset):
            ticker = yf.Ticker(asset.replace("#", ""))
            if days_before <= 1:
                period = "1d"
            elif days_before <= 5:
                period = "5d"
            elif days_before <= 30:
                period = "1mo"
            elif days_before <= 90:
                period = "3mo"
            elif days_before <= 182:
                period = "6mo"
            elif days_before <= 365:
                period = "1y"
            df = ticker.history(period=period, interval="1d")
            df.rename(columns={ "Open": "open", "Close": "close", "High": "high", "Low": "low", }, inplace=True)
            return df
        else:
            if asset in coingecko_id_to_binance.keys():
                api = BinanceAPI()
                candles = api.get_candles_by_limit(coingecko_id_to_binance[asset], "1d", limit=days_before)
                df = pd.DataFrame.from_dict(candles)
                if not with_partial_today_bar:
                    df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
                df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
                df.set_index('timestamp', inplace=True)
                return df
            return pd.DataFrame.from_dict({})

    def get_avg_price_n_days(self, asset: str, days_before: int) -> float:
        df = self._get_historical_bars(asset, days_before)
        if len(df) > 0:
            df['ma'] = talib.MA(df['close'], min(len(df), days_before))
            r = df['ma'][-1]
            if r != r:
                raise ValueError("ma == NaN")
            return r
        return self.get_market_price(asset)
