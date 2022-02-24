import time

from lib.trader import exante_api
from lib.trader.trader import Trader
from lib.common.misc import get_first_decimal_place


class ExanteTraderError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)

class ExanteTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return True

    def __init__(self, ticker: str, appid: str, clientid: str, sharedkey: str,  accountid: str, demo: bool=False):
        self._api = exante_api.Exante(appid, clientid, sharedkey, accountid, demo)
        self._sym =  self._resolve_symbol_by_ticker(ticker)
        #print(f"exante: resolved ticker={ticker} to symbol={self._sym}")

    def buy_market(self, qty: float, qty_in_usd: bool) -> tuple[float,float]:
        if qty_in_usd:
            market_price = float(self._api.get_last_quote(self._sym)['ask'])
            qty_tokens = qty / market_price
        else:
            qty_tokens = qty
        min_qty = self._api.get_min_qty(self._sym)
        qty_tokens = max(qty_tokens, min_qty)
        qty_tokens = round(qty_tokens, get_first_decimal_place(min_qty))
        return self._wait_for_order(self._api.place_market_order(sym=self._sym, side="buy", size=qty_tokens, duration="day"))

    def sell_market(self, qty_tokens: float) -> tuple[float,float]:
        return self._wait_for_order(self._api.place_market_order(syn=self._sym, side="sell", size=qty_tokens, duration="day"))

    def _wait_for_order(self, order_id: str) -> tuple[float,float]:
        if order_id is None:
            raise ExanteTraderError("order was not created")
        fill_qty = 0
        fill_price = 0
        timeout = time.time() + 10
        while True:
            r = self._api.get_order(order_id)
            if r is None:
                raise ExanteTraderError("can't query order")
            #print(r)
            status = r.order_state.status.name
            #print(status)
            if status == "cancelled":
                raise ExanteTraderError("order cancelled")
            elif status == "rejected":
                raise ExanteTraderError("order rejected")
            elif status == "filled":
                fill_qty = float(sum( [x.quantity for x in r.order_state.fills] ))
                fill_value = float(sum( [x.quantity*x.price for x in r.order_state.fills] ))
                fill_price = fill_value / fill_qty
                break
            else:
                print(".",end='')
                time.sleep(1)
                if time.time() > timeout:
                    self._api.cancel_order(order_id)
                    raise ExanteTraderError("order timeout")
        return fill_price, fill_qty,


    # def estimate_fill_price(self, qty: float, side: str) -> None:
    #     raise NotImplementedError()

    # def get_available_qty(self) -> None:
    #     raise NotImplementedError()

    def _resolve_symbol_by_ticker(self,ticker: str) -> str:
        if "." in ticker:
            return ticker

        exchs =[
            "NYSE",
            "NASDAQ",
            "ARCA",
            "BATS"
        ]
        v_symbol_exists = [ 1 if self._api.is_valid_symbol(ticker + "." + ex) else 0 for ex in exchs]
        num_symbol_instances = sum(v_symbol_exists)
        if num_symbol_instances == 0:
            raise ExanteTraderError(f"ticker {ticker} can't be resolved to symbol")
        if num_symbol_instances > 1:
            raise ExanteTraderError(f"ticker {ticker} resolves to multiple symbols")
        for i in range(len(exchs)):
            if v_symbol_exists[i]:
                return ticker + "." + exchs[i]

    