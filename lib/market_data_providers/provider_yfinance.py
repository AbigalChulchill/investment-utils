from typing import Any
from .interface import MarketDataProvider
from ..common.misc import is_stock
import pandas as pd
import yfinance as yf
import logging

yf_exclude_stocks =[ 
    "PAXG"
]

class MarketDataProviderYF(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return is_stock(asset) and asset not in yf_exclude_stocks

    def __init__(self):
        self._ticker_cache = dict()

    def _get_ticker(self, asset: str):
        if asset not in self._ticker_cache.keys():
            self._ticker_cache[asset] = yf.Ticker(asset)
        return self._ticker_cache[asset]

    def _get_history(self, asset: str, period: str, interval: str) -> Any:
        return self._get_ticker(asset).history(period=period, interval=interval)
    def _get_info(self, asset: str) -> Any:
        return self._get_ticker(asset).info

    def _get(self, asset: str, op: Any, **kwargs) -> Any:
        retries = 3
        while True:
            try:
                return op(asset, **kwargs)
            except:
                if retries > 0:
                    retries -= 1
                    logging.debug(f"YahooFinance exception - retrying, {retries} attempts remaining")
                    continue
                else:
                    raise

    def get_market_price(self, asset: str) -> float:
        return self.get_historical_bars(asset,1,True)['close'].to_numpy(float)[-1]

    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool =False)->pd.DataFrame:
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
        df = self._get(asset, self._get_history, period=period, interval="1d")
        df.rename(columns={ "Open": "open", "Close": "close", "High": "high", "Low": "low", }, inplace=True)
        return df

    def get_fundamentals(self, asset: str) -> dict:
        info = self._get(asset, self._get_info)
        d = {}
        if "trailingPE" in info.keys():
            d['P/E trailing'] = info['trailingPE']
        if "forwardPE" in info.keys():
            d['P/E forward'] = info['forwardPE']
        if "pegRatio" in info.keys():
            d['PEG'] = info['pegRatio']
        if "priceToBook" in info.keys():
            d['P/B'] = info['priceToBook']
        if "priceToSalesTrailing12Months" in info.keys():
            d['P/S'] = info['priceToSalesTrailing12Months']
        return d
