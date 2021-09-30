import time

from typing import Tuple

from . import mexc_api
from .trader import Trader


coingecko_to_symbol={
    'gitcoin':       'GTC_USDT',
    'harmony':       'ONE_USDT',
    'cosmos':        'ATOM_USDT',
    'arweave':       'AR_USDT',
}

class MexcTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in coingecko_to_symbol.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self._symbol = coingecko_to_symbol[sym]
        self._api = mexc_api.Mexc(api_key, secret)

    def buy_market(self, qty_usd: float) -> Tuple[float,float]:
        market_price = float(self._api.get_ticker(self._symbol)['ask'])
        return self._finalize_order(self._api.place_order(symbol=self._symbol, price=market_price*1.01, qty=qty_usd / market_price, trade_type="BID", order_type="IMMEDIATE_OR_CANCEL" ))

    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
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