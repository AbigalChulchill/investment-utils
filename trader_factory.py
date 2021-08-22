import trader
from poloniex_trader import PoloniexTrader
from ftx_trader import FtxTrader
from binance_trader import BinanceTrader
from okex_trader import OkexTrader
from bitrue_trader import BitrueTrader
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
        elif exch == 'binance':
            if BinanceTrader.handles_sym(sym):
                return BinanceTrader(sym)
        elif exch == 'okex':
            if OkexTrader.handles_sym(sym):
                return OkexTrader(sym)
        elif exch == 'bitrue':
            if BitrueTrader.handles_sym(sym):
                return BitrueTrader(sym)
        return DummyTrader(sym)
