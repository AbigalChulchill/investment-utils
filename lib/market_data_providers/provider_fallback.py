from typing import List, Any
from .interface import MarketDataProvider
from math import nan

class MarketDataProviderFallback(MarketDataProvider):
    def get_supported_methods(self, asset: str) -> List[str]:
        return [
            "get_market_price",
            "get_historical_bars",
            "get_market_cap",
            "get_total_supply",
            "get_fundamentals",
        ]

    def get_market_price(self, asset: str) -> float:
        return nan

    def get_historical_bars(self, asset: str, days_before: int)-> Any:
        return None

    def get_market_cap(self, asset: str) -> int:
        return nan

    def get_total_supply(self, asset: str) -> int:
        return nan

    def get_fundamentals(self, asset: str) -> dict:
        return {}
