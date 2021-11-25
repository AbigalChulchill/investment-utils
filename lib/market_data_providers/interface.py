from abc import abstractmethod
from typing import Dict
import pandas as pd

class MarketDataProvider(object):
    @abstractmethod
    def get_market_price(self, asset: str) -> float:
        """return last price the instrument was trading at"""

    @abstractmethod
    def get_historical_bars(self, asset: str, days_before: int) -> pd.DataFrame:
        """return historical bars. 
            Args:
                days_before     number of historical bars to return
            Return:
                df with at least (days_before + 1) bars, where last bar is always a partial today bar
            Examples:
                get_historical_bars(..., days_before=0)
                -> returned partial today bar

                get_historical_bars(..., days_before=1)
                -> returned a yesterday bar followed by partial today bar
        """

    @abstractmethod
    def get_fundamentals(self, asset: str) -> Dict:
        """return fundamentals. Only applicable to stocks"""
