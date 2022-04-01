import re
from typing import Tuple
from lib.trader.trader import Trader
from lib.common.market_data import MarketData
from math import ceil

class DummyTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return True

    def __init__(self, sym: str, allow_fractional_share_size: bool):
        self._fractional = allow_fractional_share_size
        self._sym_original_name = sym
        m = re.match("^(.+)-perpetual.+", sym)
        if m:
            self._sym = m[1]
        else:
            self._sym = sym

    def buy_market(self, qty: float, qty_in_usd: bool) -> Tuple[float,float]:
        market_data = MarketData()
        market_price = market_data.get_market_price(self._sym)
        qty_sym = qty / market_price if qty_in_usd else qty
        qty_sym = qty_sym if self._fractional else ceil(qty_sym)
        print(f"SIMULATE: buying {round(qty_sym,8)} {self._sym_original_name} at {round(market_price,8)}")
        return [market_price, qty_sym]

    def sell_market(self, qty_sym: float) -> Tuple[float,float]:
        market_data = MarketData()
        market_price = market_data.get_market_price(self._sym)
        qty_sym = qty_sym if self._fractional else ceil(qty_sym)
        print(f"SIMULATE: selling {round(qty_sym,8)} {self._sym_original_name} at {round(market_price,8)}")
        return [market_price, qty_sym]
