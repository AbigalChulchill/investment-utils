from lib.market_data_providers.provider_poloniex import MarketDataProviderPoloniex
from .interface import MarketDataProvider
from .provider_binance import MarketDataProviderBinance
from .provider_ftx import MarketDataProviderFTX
from .provider_poloniex import MarketDataProviderPoloniex
from .provider_yfinance import MarketDataProviderYF
from .provider_coingecko import MarketDataProviderCoingecko


class MarketDataProviderFlyweight:
    def __init__(self):
        self._prov_binance = MarketDataProviderBinance()
        self._prov_ftx = MarketDataProviderFTX()
        self._prov_poloniex = MarketDataProviderPoloniex()
        self._prov_yf = MarketDataProviderYF()
        self._prov_cg = MarketDataProviderCoingecko()
    
    def get(self, asset: str) -> MarketDataProvider:
        if MarketDataProviderBinance.handles(asset):
            return self._prov_binance
        elif MarketDataProviderYF.handles(asset):
            return self._prov_yf
        elif MarketDataProviderFTX.handles(asset):
            return self._prov_ftx
        elif MarketDataProviderPoloniex.handles(asset):
            return self._prov_poloniex
        elif MarketDataProviderCoingecko.handles(asset):
            return self._prov_cg
        raise ValueError(f"{asset} market data unobtainable")
