import trader
from poloniex_trader import PoloniexTrader
from dummy_trader import DummyTrader


class TraderFactory:
    @staticmethod
    def create_trader(sym: str) -> trader.Trader:
        if PoloniexTrader.handles_sym(sym):
            return PoloniexTrader(sym)
        else:
            return DummyTrader(sym)
