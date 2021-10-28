import pandas as pd

class MarketDataProvider(object):

    def get_market_price(self, asset: str) -> float:
        raise NotImplementedError()

    def get_historical_bars(self, asset: str, days_before: int, with_partial_today_bar:bool=False) -> pd.DataFrame:
        raise NotImplementedError()

    def get_fundamentals(self, asset: str) -> dict:
        raise NotImplementedError()
