from .interface import MarketDataProvider
from ..common.misc import is_metal, is_stock

import pycoingecko
import pandas as pd

class MarketDataProviderCoingecko(MarketDataProvider):

    @staticmethod
    def handles(asset: str):
        return not is_metal(asset) and not is_stock(asset)

    def __init__(self):
        self._cg = pycoingecko.CoinGeckoAPI()

    def get_market_price(self, asset: str) -> float:
        price_data = self._cg.get_price(ids=[asset], vs_currencies='usd', include_24hr_change="false")
        return float(price_data[asset]['usd'])

    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool =False)->pd.DataFrame:
        return pd.DataFrame()
