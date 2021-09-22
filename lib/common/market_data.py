import pycoingecko
import talib
import pandas as pd
import yfinance as yf
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

    def get_24h_change(self, asset: str) -> float:
        if is_stock(asset):
            return 0
        else:
            return float(self._price_data[asset]['usd_24h_change'])

    def _get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
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
            df.rename(columns={ "Open": "open", "Close": "close", "High": "high", "Low": "low", }, inplace=True)
            return df
        else:
            api = BinanceAPI()
            candles = api.get_candles_by_limit(coingecko_id_to_binance[asset], "1d", limit=days_before)
            df = pd.DataFrame.from_dict(candles)
            df = df[:-1] # remove last item as it corresponds to just opened candle (partial)
            df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
            df.set_index('timestamp', inplace=True)
            return df

    def get_avg_price_n_days(self, asset: str, days_before: int) -> float:
        df = self._get_historical_bars(asset, days_before)
        df['ma'] = talib.MA(df['close'], min(len(df), days_before))
        r = df['ma'][-1]
        if r != r:
            raise ValueError("ma == NaN")
        return r


    def is_dipping(self, asset: str) -> dict:
        df = self._get_historical_bars(asset, 3)
        bar0 = df.iloc[-1]
        bar1 = df.iloc[-2]
        open0 = float(bar0['open'])
        open1 = float(bar1['open'])
        close0 = float(bar0['close'])
        close1 = float(bar1['close'])

        #1) last day was red candle
        # or
        #2) last day was gren candle but it closed (gapped) below last-1 day close. This usually indicates bullish reversal
        # return (bar0['close'] < bar0['open']) or \
        #        (bar0['close'] > bar0['open'] and bar0['close'] < bar1['close'])

        # two red bars in a row or red bar that is too large
        return (close1 < open1) and (close0 < open0)\
                or \
                (close0 < open0 and ((open0-close0)/open0 > 0.05)  )
