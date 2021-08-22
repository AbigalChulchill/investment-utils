from trader import Trader
import okex_api, okex_config
import time

sym_to_market={
    'decentraland':       'MANA-USDT',
}

class OkexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_market.keys()

    def __init__(self, sym: str):
        self.market = sym_to_market[sym]
        self.api = okex_api.Okex(okex_config.API_KEY, okex_config.SECRET, okex_config.PASS)

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