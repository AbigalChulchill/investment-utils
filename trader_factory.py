import trader
from poloniex_trader import PoloniexTrader
from dummy_trader import DummyTrader


class TraderFactory:
    @staticmethod
    def create_trader(sym: str, exch: str) -> trader.Trader:
        if exch == 'poloniex':
            if PoloniexTrader.handles_sym(sym):
                return PoloniexTrader(sym)

        return DummyTrader(sym)
