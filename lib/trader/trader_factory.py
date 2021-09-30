from .trader import Trader
from .poloniex_trader import PoloniexTrader
from .ftx_trader import FtxTrader
from .okex_trader import OkexTrader
from .bitrue_trader import BitrueTrader
from .mexc_trader import MexcTrader
from .dummy_trader import DummyTrader
from .api_keys_config import ApiKeysConfig

class TraderFactory:
    @staticmethod
    def create_dca(sym: str, exch: str) -> Trader:
        cfg = ApiKeysConfig()
        if exch == 'poloniex':
            if PoloniexTrader.handles_sym(sym):
                api_key, secret = cfg.get_poloniex_ks()
                return PoloniexTrader(sym, api_key, secret)
        elif exch == 'ftx':
            if FtxTrader.handles_sym(sym):
                api_key, secret = cfg.get_ftx_ks()
                subaccount = cfg.get_ftx_subaccount_dca()
                return FtxTrader(sym, api_key, secret, subaccount)
        elif exch == 'okex':
            if OkexTrader.handles_sym(sym):
                api_key, secret, password = cfg.get_okex_ksp()
                return OkexTrader(sym, api_key, secret, password)
        elif exch == 'bitrue':
            if BitrueTrader.handles_sym(sym):
                api_key, secret = cfg.get_bitrue_ks()
                return BitrueTrader(sym, api_key, secret)
        elif exch == 'mexc':
            if MexcTrader.handles_sym(sym):
                api_key, secret = cfg.get_mexc_ks()
                return MexcTrader(sym, api_key, secret)
        raise ValueError(f"{sym} can't be traded")

    def create_trading_real(sym: str) -> Trader:
        cfg = ApiKeysConfig()
        api_key, secret = cfg.get_ftx_ks()
        subaccount = cfg.get_ftx_subaccount_trade()
        return FtxTrader(sym, api_key, secret, subaccount)

    def create_dummy(sym: str) -> Trader:
        return DummyTrader(sym)
