import pycoingecko

class MarketPrice:
    def __init__(self, coin_ids: list[str] = None):
        cg = pycoingecko.CoinGeckoAPI()
        self.price_data = cg.get_price(ids=coin_ids, vs_currencies='usd')

    def get_market_price(self, coin: str) -> float:
        return float(self.price_data[coin]['usd'])
