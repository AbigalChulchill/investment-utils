import time

from typing import Tuple

from lib.common.id_map_ftx import id_to_ftx
from lib.common.orderbook import estimate_fill_price, FillPriceEstimate
from lib.trader import ftx_api
from lib.trader.trader import Trader

# limit price estimate is based on (qty requested) x (overcommit_factor)
overcommit_factor = 1.1

class FtxTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_ftx.keys()

    def __init__(self, sym: str, api_key: str, secret: str, subaccount: str):
        self._market = id_to_ftx[sym]
        self._api = ftx_api.Ftx(api_key, secret, subaccount)

    def buy_market(self, qty: float, qty_in_usd: bool) -> Tuple[float,float]:
        if qty_in_usd:
            market_price = self._api.get_ticker(self._market)
            qty_tokens = qty / market_price
        else:
            qty_tokens = qty
        min_qty = self._api.get_min_qty(self._market)
        qty_tokens = max(qty_tokens, min_qty)
        return self._finalize_order(self._api.place_order(market=self._market, side="buy", price=None, limit_or_market="market", size=qty_tokens, ioc=False))

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
        
    def estimate_fill_price(self, qty: float, side: str) -> FillPriceEstimate:
        assert side in ["buy", "sell"]
        if side == "buy":
            return estimate_fill_price(self._api.get_orderbook(market=self._market)['asks'], qty*overcommit_factor)
        else:
            return estimate_fill_price(self._api.get_orderbook(market=self._market)['bids'], qty*overcommit_factor)