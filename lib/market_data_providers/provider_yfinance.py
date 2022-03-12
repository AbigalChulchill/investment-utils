
# FIXME
# workaround until this is fixed
# .local/lib/python3.10/site-packages/yahoo_fin/stock_info.py:302: FutureWarning: The frame.append method is deprecated and will be removed from pandas in a future version. Use pandas.concat instead.
import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

import datetime, pathlib, pickledb
from math import nan, isclose
from typing import Any
import pandas as pd
import yahoo_fin.stock_info as yfsi
import logging
from .interface import MarketDataProvider
from lib.common.misc import is_crypto


class StockInfoDb:
    def __init__(self):
        pathlib.Path("cache/yf").mkdir(parents=True, exist_ok=True)
        self.db = pickledb.load(f"cache/yf/info_{datetime.datetime.utcnow().strftime('%Y-%m-%d')}.db", auto_dump=True)
    def get_info(self, ticker: str) -> str:
        existing_data = self.db.get(ticker)
        if existing_data:
            return existing_data
        else:
            data ={}
            try:
                data = yfsi.get_quote_data(ticker)
                data |= yfsi.get_quote_table(ticker)
                for _,cols in yfsi.get_stats(ticker).iterrows():
                    data[cols['Attribute']] = cols['Value']
            except:
                pass
            
            self.db.set(ticker, data)
            return data


class CompanyInfoDb:
    def __init__(self):
        pathlib.Path("cache/yf").mkdir(parents=True, exist_ok=True)
        self.db = pickledb.load(f"cache/yf/companyinfo.db", auto_dump=True)
    def get_company_info(self, ticker: str) -> str:
        existing_data = self.db.get(ticker)
        if existing_data:
            return existing_data
        else:
            try:
                data = {}
                for index,cols in yfsi.get_company_info(ticker).iterrows():
                    data[index] = cols['Value']
            except:
                pass
            self.db.set(ticker, data)
            return data


def decode_float_value(v: float, precision: int) -> float:
    return round(v,precision)


def decode_float_value_non_zero(v: float, precision: int) -> float:
    v = float(v)
    if isclose(0, v):
        v = nan
    return round(v, precision)


def decode_yf_percent_value(v: str, precision: int) -> float:
    try:
        v = v.replace("%","")
    except:
        pass
    v = float(v)
    if isclose(0, v):
        v = nan
    return round(v, precision)


class MarketDataProviderYF(MarketDataProvider):
    def __init__(self):
        self._stock_info_db = StockInfoDb()
        self._company_info_db = CompanyInfoDb()

    def get_supported_methods(self, asset: str) -> list[str]:
        if not is_crypto(asset):
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
        return yfsi.get_data(ticker=asset,start_date=d_start, end_date=None, interval=interval)

    def _get_info(self, asset: str) -> Any:
        return self._stock_info_db.get_info(asset)

    def _get_companyinfo(self, asset: str) -> Any:
        return self._company_info_db.get_company_info(asset)

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
        return yfsi.get_live_price(asset)

    def get_market_cap(self, asset: str) -> int:
        info = self._get(asset, self._get_info)
        return decode_float_value_non_zero(info ['marketCap'], precision=1) if 'marketCap' in info else nan

    def get_total_supply(self, asset: str) -> int:
        info = self._get(asset, self._get_info)
        return decode_float_value_non_zero(info ['sharesOutstanding'], precision=1) if 'sharesOutstanding' in info else nan

    def get_historical_bars(self, asset: str, days_before: int)->pd.DataFrame:

        df = self._get(asset, self._get_history, days=days_before, interval="1d")
        df.rename(columns={ "Open": "open", "Close": "close", "High": "high", "Low": "low", }, inplace=True)
        return df

    def get_fundamentals(self, asset: str) -> dict:
        info = self._get(asset, self._get_info)
        companyinfo = self._get(asset, self._get_companyinfo)
        d = {}
        if "trailingPE" in info:                    d['tr P/E'] = decode_float_value(info['trailingPE'], precision=1)
        if "forwardPE" in info:                     d['fw P/E'] = decode_float_value(info['forwardPE'], precision=1)
        if "priceToBook" in info:                   d['P/B'] = decode_float_value(info['priceToBook'], precision=1)
        if "Total Debt/Equity (mrq)" in info:       d['d/e'] = decode_float_value_non_zero(info['Total Debt/Equity (mrq)'], precision=1)
        if "trailingAnnualDividendRate" in info:    d['div rate'] = decode_float_value_non_zero(info['trailingAnnualDividendRate'], precision=2)
        if "trailingAnnualDividendYield" in info:   d['div yield,%'] = decode_float_value_non_zero(info['trailingAnnualDividendYield']*100, precision=1)
        if "Yield" in info:                         d['div yield,%'] = decode_yf_percent_value(info['Yield'], precision=1)
        if "Expense Ratio (net)" in info:           d['expense,%'] = decode_yf_percent_value(info['Expense Ratio (net)'], precision=1)
        if "sector" in companyinfo:                 d['sector'] = companyinfo['sector']
        if "industry" in companyinfo:               d['industry'] = companyinfo['industry']
        return d
