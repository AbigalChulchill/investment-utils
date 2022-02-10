
import datetime, pathlib, pickledb
from math import nan
from typing import List, Any
import pandas as pd
import yahoo_fin.stock_info
import logging
from .interface import MarketDataProvider
from lib.common.misc import is_crypto

yf_exclude_stocks =[ 
    "PAXG"
]


class StockInfoDb:
    def __init__(self):
        pathlib.Path("cache/yf").mkdir(parents=True, exist_ok=True)
        self.db = pickledb.load(f"cache/yf/info_{datetime.datetime.utcnow().strftime('%Y-%m-%d')}.db", auto_dump=True)
    def get_info(self, ticker: str) -> str:
        existing_name = self.db.get(ticker)
        if existing_name:
            return existing_name
        else:
            try:
                name = yahoo_fin.stock_info.get_quote_data(ticker)
            except:
                name = ticker
            self.db.set(ticker, name)
            return name



class MarketDataProviderYF(MarketDataProvider):
    def __init__(self):
        self._stock_info_db = StockInfoDb()

    def get_supported_methods(self, asset: str) -> List[str]:
        if not is_crypto(asset) and asset not in yf_exclude_stocks:
            return [
                "get_market_price",
                "get_historical_bars",
                "get_fundamentals",
                "get_market_cap",
                "get_total_supply",
            ]
        else:
            return []

    def _get_history(self, asset: str, days: int, interval: str) -> Any:
        d_start = datetime.datetime.utcnow().timestamp() - days*60*60*24
        return yahoo_fin.stock_info.get_data(ticker=asset,start_date=d_start, end_date=None, interval=interval)

    def _get_info(self, asset: str) -> Any:
        return self._stock_info_db.get_info(asset)

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

        df = self._get(asset, self._get_history, days=days_before, interval="1d")
        df.rename(columns={ "Open": "open", "Close": "close", "High": "high", "Low": "low", }, inplace=True)
        return df

    def get_fundamentals(self, asset: str) -> dict:
        info = self._get(asset, self._get_info)
        d = {}
        if "trailingPE" in info and info['trailingPE'] is not None:
            d['P/E trailing'] = round(info['trailingPE'],1)
        if "forwardPE" in info and info['forwardPE'] is not None:
            d['P/E forward'] = round(info['forwardPE'],1)
        # if "pegRatio" in info and info['pegRatio'] is not None:
        #     d['PEG'] = round(info['pegRatio'],1)
        if "priceToBook" in info and info['priceToBook'] is not None:
            d['P/B'] = round(info['priceToBook'],1)
        # if "priceToSalesTrailing12Months" in info and info['priceToSalesTrailing12Months'] is not None:
        #     d['P/S'] = round(info['priceToSalesTrailing12Months'],1)
        if "trailingAnnualDividendRate" in info and info['trailingAnnualDividendRate'] is not None:
            d['div rate'] = round(info['trailingAnnualDividendRate'],2)
        if "trailingAnnualDividendYield" in info and info['trailingAnnualDividendYield'] is not None:
            d['div yield, %'] = round(info['trailingAnnualDividendYield']*100,1)

        return d
