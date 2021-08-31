import time
from . import bitrue_api
from .trader import Trader


sym_to_pair={
    'gitcoin':       'GTCUSDT',
}

sym_round_decimals={
    'gitcoin':       2,
}

class BitrueTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_pair.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self._pair = sym_to_pair[sym]
        self._round_decimals = sym_round_decimals[sym]
        self._api = bitrue_api.Bitrue(api_key, secret)

    def _round_qty(self, qty: float) -> float:
        return round(qty, self._round_decimals)

    def buy_market(self, qty_usd: float) -> float:
        market_price = float(self._api.get_orderbook(self._pair)['asks'][0][0])
        order_id = self._api.new_order(symbol=self._pair, side="BUY", qty=self._round_qty(qty_usd / market_price))
        return self._wait_for_order(order_id)

    def sell_market(self, qty_tokens: float) -> float:
        order_id = self._api.new_order(symbol=self._pair, side="SELL", qty=self._round_qty(qty_tokens))
        return self._wait_for_order(order_id)

    def _wait_for_order(self, order_id: int):
        while True: #fixme: timeout maybe? shouldn't be needed
            time.sleep(1)
            response = self._api.query_order(self._pair, order_id)
            status = response['status']
            if status == "FILLED":
                fill_qty = float(response['executedQty'])
                fill_quote = float(response['cummulativeQuoteQty'])
                return [fill_quote / fill_qty, fill_qty]
            elif status == "CANCELED" or status == "REJECTED" or status == "EXPIRED" :
                raise f"not filled : {response}"
            else:
                print("waiting on trade ...")