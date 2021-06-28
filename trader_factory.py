import trader
from poloniex_trader import PoloniexTrader
from ftx_trader import FtxTrader
from dummy_trader import DummyTrader


class TraderFactory:
    @staticmethod
    def create_trader(sym: str, exch: str) -> trader.Trader:
        if exch == 'poloniex':
            if PoloniexTrader.handles_sym(sym):
                return PoloniexTrader(sym)
        elif exch == 'ftx':
            if FtxTrader.handles_sym(sym):
                return FtxTrader(sym)

        return DummyTrader(sym)
