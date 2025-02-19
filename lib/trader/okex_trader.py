from lib.common.id_map_okex import id_to_okex
from lib.common.id_ticker_map import id_to_ticker
from lib.trader import okex_api
from lib.trader.trader import Trader
from lib.common.orderbook import estimate_fill_price, FillPriceEstimate

class OkexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_okex.keys()

    def __init__(self, sym: str, api_key: str, secret: str, passw: str):
        self.market = id_to_okex[sym]
        self.ticker = id_to_ticker[sym]
        self.api = okex_api.Okex(api_key, secret, passw)

    def buy_market(self, qty: float, qty_in_usd: bool) -> tuple[float,float]:
        if qty_in_usd:
            market_price = float(self.api.get_ticker(self.market)[0]['askPx'])
            qty_tokens = qty / market_price
        else:
            qty_tokens = qty
        min_qty = self.api.get_min_qty(self.market)
        qty_tokens = max(qty_tokens, min_qty)
        order_id = self.api.place_order(market=self.market, side="buy", size=qty_tokens)
        return self._wait_for_order(order_id)

    def sell_market(self, qty_tokens: float) -> tuple[float,float]:
        order_id = self.api.place_order(market=self.market, side="sell", size=qty_tokens)
        return self._wait_for_order(order_id)

    def _wait_for_order(self, order_id: int) -> tuple[float,float]:
        while True: #fixme: timeout maybe? shouldn't be needed
            r = self.api.get_order_details(self.market, order_id)
            if r['state'] == "filled":
                if r['side'] == "buy":
                    # if buying fee is deducted from token qty bought
                    fill_qty = float(r['accFillSz']) + float(r['fee']) 
                    fill_price  = float(r['avgPx'])
                elif r['side'] == "sell":
                    # if selling fee is deducted from USD amount sold
                    fill_qty = float(r['accFillSz'])
                    fill_price = float(r['avgPx']) + float(r['fee']) / fill_qty
                else:
                    raise ValueError("invalid side")
                return [fill_price, fill_qty]
            elif r['state'] == "canceled":
                raise ValueError("not filled")
            else:
                print("waiting on trade ...")

    def estimate_fill_price(self, qty: float, side: str) -> FillPriceEstimate:
        assert side in ["buy", "sell"]
        if side == "buy":
            return estimate_fill_price(self.api.get_orderbook(self.market,'asks'), qty)
        else:
            return estimate_fill_price(self.api.get_orderbook(self.market,'bids'), qty)

    def get_available_qty(self) -> float:
        balances = self.api.get_balances()
        free = [x['eq'] for x in balances if x['ccy'] == self.ticker]
        return float(free[0])