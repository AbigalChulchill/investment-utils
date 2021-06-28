from trader import Trader
from market_price import MarketPrice

class DummyTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return True

    def __init__(self, sym: str):
        self.sym = sym

    def buy_market(self, qty_usd: float) -> float:
        mp = MarketPrice(self.sym)
        market_price = mp.get_market_price(self.sym)
        print(f"Now you must go ahead and buy manually {self.sym} for ${qty_usd} at price {market_price}")
        return [market_price, qty_usd / market_price]
