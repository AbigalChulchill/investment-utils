import pycoingecko

class MarketData:
    def __init__(self, coin_ids: list[str] = None):
        cg = pycoingecko.CoinGeckoAPI()

        # caching price data for all available coins at once
        # so we don't call API for every single item (because of frequency limits)

        self.price_data = cg.get_price(ids=coin_ids, vs_currencies='usd', include_24hr_change="true")

    def get_market_price(self, coin: str) -> float:
        return float(self.price_data[coin]['usd'])

    def get_24h_change(self, coin: str) -> float:
        return float(self.price_data[coin]['usd_24h_change'])
