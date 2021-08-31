import re
from .trader import Trader
from lib.common.market_data import MarketData

class DummyTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return True

    def __init__(self, sym: str):
        self._sym_original_name = sym
        m = re.match("^(.+)-perpetual.+", sym)
        if m:
            self._sym = m[1]
        else:
            self._sym = sym

    def buy_market(self, qty_usd: float) -> float:
        market_data = MarketData(self._sym)
        market_price = market_data.get_market_price(self._sym)
        qty_sym =  qty_usd / market_price
        print(f"buying {qty_sym} {self._sym_original_name} at {market_price}")
        return [market_price, qty_sym]

    def sell_market(self, qty_sym: float) -> float:
        market_data = MarketData(self._sym)
        market_price = market_data.get_market_price(self._sym)
        print(f"selling {qty_sym} {self._sym_original_name} at {market_price}")
        return [market_price, qty_sym]
