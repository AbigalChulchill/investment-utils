from lib.market_data_providers.provider_poloniex import MarketDataProviderPoloniex
from .interface import MarketDataProvider
from .provider_binance import MarketDataProviderBinance
from .provider_ftx import MarketDataProviderFTX
from .provider_poloniex import MarketDataProviderPoloniex
from .provider_yfinance import MarketDataProviderYF
from .provider_coingecko import MarketDataProviderCoingecko
from .provider_fallback import MarketDataProviderFallback


class MarketDataProviderFlyweight:
    def __init__(self):
        self._map = {
            "binance": MarketDataProviderBinance(),
            "ftx": MarketDataProviderFTX(),
            "poloniex": MarketDataProviderPoloniex(),
            "yf": MarketDataProviderYF(),
            "cg": MarketDataProviderCoingecko(),
            "fallback": MarketDataProviderFallback(),
        }
        self._prioritylist = [
            "binance",
            "ftx",
            "poloniex",
            "yf",
            "cg",
            "fallback",
        ]
    
    def get(self, asset: str, method: str) -> MarketDataProvider:
        for id in self._prioritylist:
            prov = self._map[id]
            if method in prov.get_supported_methods(asset):
                #print(f"MarketDataProvider: {method}({asset}) handled by {id}")
                return prov
        raise ValueError(f"{asset} market data unobtainable")
