from lib.market_data_providers.provider_poloniex import MarketDataProviderPoloniex
from .interface import MarketDataProvider
from .provider_binance import MarketDataProviderBinance
from .provider_ftx import MarketDataProviderFTX
from .provider_poloniex import MarketDataProviderPoloniex
from .provider_yfinance import MarketDataProviderYF
from .provider_coingecko import MarketDataProviderCoingecko


class MarketDataProviderFlyweight:
    def __init__(self):
        self._map = {
            "binance": MarketDataProviderBinance(),
            "ftx": MarketDataProviderFTX(),
            "poloniex": MarketDataProviderPoloniex(),
            "yf": MarketDataProviderYF(),
            "cg": MarketDataProviderCoingecko(),
        }
        self._prioritylist = [
            "binance",
            "ftx",
            "poloniex",
            "yf",
            "cg",
        ]
    
    def get(self, asset: str) -> MarketDataProvider:
        for id in self._prioritylist:
            prov = self._map[id]
            if prov.handles(asset):
                #print(f"MarketDataProvider: id {asset} handled by {id}")
                return prov
        raise ValueError(f"{asset} market data unobtainable")
