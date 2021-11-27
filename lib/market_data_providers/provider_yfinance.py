
import re, os, datetime, pathlib, json
from math import nan
from typing import List, Dict, Any
import pandas as pd
import yfinance as yf
import yahoo_fin.stock_info
import logging
from .interface import MarketDataProvider
from lib.common.misc import is_stock
from lib.common.msg import warn

yf_exclude_stocks =[ 
    "PAXG"
]


class YFInfoCache:
    _cache_dir = f"cache/yf/info/{datetime.datetime.utcnow().strftime('%Y-%m-%d')}"

    def __init__(self):
        self._cache = {}

    @staticmethod
    def _get_cache_file_name(asset: str):
        return f"{YFInfoCache._cache_dir}/{asset}.json"

    def put(self, asset: str, d: Dict[Any,Any]):
        self._cache[asset] = d
        if not os.path.exists(YFInfoCache._cache_dir):
            pathlib.Path(YFInfoCache._cache_dir).mkdir(parents=True, exist_ok=True)
        cache_file = YFInfoCache._get_cache_file_name(asset)
        with open(cache_file, "w") as f:
            json.dump(d, f)

    def get(self, asset: str) -> Dict[Any,Any]:
        if asset in self._cache.keys():
            return self._cache[asset]
        cache_file = YFInfoCache._get_cache_file_name(asset)
        if os.path.exists(cache_file):
            return json.load(open(cache_file))
        else:
            return None

class MarketDataProviderYF(MarketDataProvider):
    def __init__(self):
        self._ticker_cache = {}
        self._info_cache = YFInfoCache()

    def get_supported_methods(self, asset: str) -> List[str]:
        if is_stock(asset) and asset not in yf_exclude_stocks:
            return [
                "get_market_price",
                "get_historical_bars",
                "get_fundamentals",
                "get_market_cap",
                "get_total_supply",
            ]
        else:
            return []

    def _get_ticker(self, asset: str):
        if asset not in self._ticker_cache.keys():
            self._ticker_cache[asset] = yf.Ticker(asset)
        return self._ticker_cache[asset]

    def _get_history(self, asset: str, period: str, interval: str) -> Any:
        return self._get_ticker(asset).history(period=period, interval=interval)
    def _get_info(self, asset: str) -> Any:
        data = self._info_cache.get(asset)
        if data is None:
            data = self._get_ticker(asset).info
            self._info_cache.put(asset, data)
        return data

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
        return yahoo_fin.stock_info.get_live_price(asset)

    def get_market_cap(self, asset: str) -> int:
        info = self._get(asset, self._get_info)
        return info ['marketCap'] if ('marketCap' in info and info['marketCap'] is not None ) else nan

    def get_total_supply(self, asset: str) -> int:
        info = self._get(asset, self._get_info)
        return info ['sharesOutstanding'] if ('sharesOutstanding' in info and info['sharesOutstanding'] is not None ) else nan

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:
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
