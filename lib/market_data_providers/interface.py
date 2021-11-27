from abc import abstractmethod
from typing import List, Dict
import pandas as pd

class MarketDataProvider(object):
    @abstractmethod
    def get_supported_methods(self, asset: str) -> List[str]:
        """return a list of supported methods for the asset"""

    @abstractmethod
    def get_market_price(self, asset: str) -> float:
        """return last price the instrument was trading at"""

    @abstractmethod
    def get_market_cap(self, asset: str) -> int:
        """return market cap in USD"""

    @abstractmethod
    def get_max_supply(self, asset: str) -> int:
        """return coin max supply"""

    @abstractmethod
    def get_historical_bars(self, asset: str, days_before: int) -> pd.DataFrame:
        """return historical 1d bars
            Args:
                days_before     number of historical bars to return
            Return:
                ohlcvt DataFrame of length (days_before + 1) bars, where last bar is always an unclosed today bar.
                May return fewer bars than requested. This might happen if the asset is younger than days_before,
                also some providers have limited history.
            Examples:
                get_historical_bars(..., days_before=0)
                -> returned partial today bar

                get_historical_bars(..., days_before=1)
                -> returned a yesterday bar followed by partial today bar
        """
    @abstractmethod
    def get_fundamentals(self, asset: str) -> Dict:
        """return fundamentals. Only applicable to stocks"""
