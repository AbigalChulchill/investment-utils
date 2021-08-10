import pycoingecko

class MarketData:
    def __init__(self):
        self.cg = pycoingecko.CoinGeckoAPI()
        data = self.cg.get_coins_markets('usd')
        self.data = dict()
        max_cap = 0
        for i in data:
            self.data[i['id']] = i
            max_cap = max(max_cap, int(i['market_cap']))
        for i in self.data.keys():
            self.data[i]['market_cap_n'] = self.data[i]['market_cap'] / float(max_cap)

    def get_market_price(self, coin: str) -> float:
        return float(self.cg.get_price(ids=coin,vs_currencies='usd')[coin]['usd'])

    def get_norm_market_cap(self, coin: str) -> float:
        return self.data[coin]['market_cap_n']
