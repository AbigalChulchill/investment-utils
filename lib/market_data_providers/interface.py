from abc import abstractmethod
from typing import Dict
import pandas as pd

class MarketDataProvider(object):
    @abstractmethod
    def get_market_price(self, asset: str) -> float:
        """return current price"""

    @abstractmethod
    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool=False) -> pd.DataFrame:
        """return historical bars"""

    @abstractmethod
    def get_fundamentals(self, asset: str) -> Dict:
        """return fundamentals"""
