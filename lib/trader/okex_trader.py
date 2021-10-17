import time
from lib.common.id_map_okex import id_to_okex
from lib.trader import okex_api
from lib.trader.trader import Trader

class OkexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_okex.keys()

    def __init__(self, sym: str, api_key: str, secret: str, passw: str):
        self.market = id_to_okex[sym]
        self.api = okex_api.Okex(api_key, secret, passw)

    def buy_market(self, qty_usd: float) -> float:
        market_price = float(self.api.get_ticker(self.market)[0]['askPx'])
        order_id = self.api.place_order(market=self.market, side="buy", size= qty_usd / market_price)
        return self._wait_for_order(order_id)

    def sell_market(self, qty_tokens: float) -> float:
        order_id = self.api.place_order(market=self.market, side="sell", size=qty_tokens)
        return self._wait_for_order(order_id)

    def _wait_for_order(self, order_id: int):
        while True: #fixme: timeout maybe? shouldn't be needed
            time.sleep(1)
            response = self.api.get_order_details(self.market, order_id)
            if response['state'] == "filled":
                fill_qty = float(response['accFillSz'])
                fill_price  = float(response['avgPx'])
                return [fill_price, fill_qty]
            elif response['state'] == "canceled":
                raise "not filled"
            else:
                print("waiting on trade ...")