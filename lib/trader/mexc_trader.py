import time

from typing import Tuple

from lib.common.msg import info,warn
from lib.common.id_map_mexc import id_to_mexc
from lib.trader import mexc_api
from lib.trader.trader import Trader


class MexcTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_mexc.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self._symbol = id_to_mexc[sym]
        self._api = mexc_api.Mexc(api_key, secret)

    def buy_market(self, qty_usd: float) -> Tuple[float,float]:
        self._check_mx_balance()
        market_price = float(self._api.get_ticker(self._symbol)['ask'])
        return self._finalize_order(self._api.place_order(symbol=self._symbol, price=market_price*1.01, qty=qty_usd / market_price, trade_type="BID", order_type="IMMEDIATE_OR_CANCEL" ))

    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        self._check_mx_balance()
        market_price = float(self._api.get_ticker(self._symbol)['bid'])
        return self._finalize_order(self._api.place_order(symbol=self._symbol, price=market_price*0.99, qty=qty_tokens, trade_type="ASK", order_type="IMMEDIATE_OR_CANCEL"))

    def _finalize_order(self, order_id: str) -> Tuple[float,float]:
        fill_qty = 0
        fill_price = 0
        for _ in range(10):
            time.sleep(0.5)
            r = self._api.query_order(self._symbol, order_id)
            if r['state'] == "FILLED":
                fill_qty = float(r['deal_quantity'])
                fill_price = float(r['deal_amount']) / fill_qty
                break
        return fill_price, fill_qty,

    def _check_mx_balance(self):
        balances = self._api.get_balances()
        get_mx_balance = lambda : float(balances['MX']['available']) if 'MX' in balances.keys() else 0
        qty = get_mx_balance()
        market_price = float(self._api.get_ticker("MX_USDT")['ask'])
        if qty * market_price < 5:
            add_qty = 10 / market_price
            info(f"mexc_trader: buying {add_qty:.1f} additional MX tokens")
            self._api.place_order(symbol="MX_USDT", price=market_price*1.01, qty=add_qty, trade_type="BID", order_type="IMMEDIATE_OR_CANCEL" )
            time.sleep(1)
            new_qty = get_mx_balance()
            if new_qty < add_qty:
                warn("mexc_trader: failed to buy MX tokens")
