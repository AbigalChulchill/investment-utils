import time

from typing import Tuple

from . import ftx_api
from .trader import Trader
from ..common.ftx_id_map import id_to_ftx


class FtxTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_ftx.keys()

    def __init__(self, sym: str, api_key: str, secret: str, subaccount: str):
        self._market = id_to_ftx[sym]
        self._api = ftx_api.Ftx(api_key, secret, subaccount)

    def buy_market(self, qty_usd: float) -> Tuple[float,float]:
        market_price = self._api.get_orderbook(self._market)['asks'][0][0]
        return self._finalize_order(self._api.place_order(market=self._market, side="buy", price=None, limit_or_market="market", size= qty_usd / market_price, ioc=False))

    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        return self._finalize_order(self._api.place_order(market=self._market, side="sell", price=None, limit_or_market="market", size=qty_tokens, ioc=False))


    def _finalize_order(self, order_id: int) -> Tuple[float,float]:
        fill_qty = 0
        fill_price = 0
        for _ in range(10):
            time.sleep(0.5)
            r = self._api.get_order_status(order_id)
            if r['status'] == "closed":
                fill_qty = float(r['filledSize'])
                fill_price = float(r['avgFillPrice'])
                break
        return fill_price, fill_qty,
        
