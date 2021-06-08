import trader
import poloniex_trader


class TraderFactory:
    @staticmethod
    def create_trader(sym: str) -> trader.Trader:
        if poloniex_trader.PoloniexTrader.handles_sym(sym):
            return poloniex_trader.PoloniexTrader(sym)
        else:
            return None
