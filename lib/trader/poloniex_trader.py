import time
from typing import List,Tuple
from lib.common.msg import info, warn
from lib.common.id_map_poloniex import id_to_poloniex
from lib.common.orderbook import estimate_fill_price
from lib.trader import poloniex_api
from lib.trader.trader import Trader

# limit price estimate is based on (qty requested) x (overcommit_factor)
overcommit_factor = 2.0

class PoloniexTraderError(RuntimeError):
    def __init__(self, message: str):
        super().__init__(message)

class PoloniexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_poloniex.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self.pair = id_to_poloniex[sym]
        self.api = poloniex_api.Poloniex(api_key, secret)

    def _handle_trade(self, response: dict) -> Tuple[float,float]:
        if 'resultingTrades' in response.keys():
            trades = response['resultingTrades']
            total_qty_coin = sum( [float(x['amount']) for x in trades] )
            total_qty_usd = sum( [float(x['total']) for x in trades] )
            fill_price = total_qty_usd / total_qty_coin
            return [fill_price, total_qty_coin]
        elif 'error' in response.keys():
            raise PoloniexTraderError(response['error'])
        else:
            raise PoloniexTraderError(f"unknown error : {response}")


    def buy_market(self, qty: float, qty_in_usd: bool) -> Tuple[float,float]:
        self._check_trx_balance()
        if qty_in_usd:
            qty_tokens = qty / self.api.returnTicker(self.pair)
        else:
            qty_tokens = qty
        limit_price = estimate_fill_price(self.api.returnOrderBook(self.pair)['asks'], qty_tokens*overcommit_factor)
        response = self.api.buy(self.pair, limit_price, qty_tokens, {'fillOrKill': True})
        return self._handle_trade(response)

    def sell_market(self, qty_tokens: float) -> Tuple[float,float]:
        self._check_trx_balance()
        limit_price = estimate_fill_price(self.api.returnOrderBook(self.pair)['bids'], qty_tokens*overcommit_factor)
        response = self.api.sell(self.pair, limit_price, qty_tokens, {'fillOrKill': True})
        return self._handle_trade(response)

    def estimate_fill_price(self, qty: float, side: str) -> float:
        assert side in ["buy", "sell"]
        if side == "buy":
            return estimate_fill_price(self.api.returnOrderBook(self.pair)['asks'], qty*overcommit_factor)
        else:
            return estimate_fill_price(self.api.returnOrderBook(self.pair)['bids'], qty*overcommit_factor)


    def _check_trx_balance(self):
        qty = float(self.api.returnBalances()['TRX'])
        market_price = float(self.api.returnOrderBook("USDT_TRX")['asks'][1][0])
        if qty * market_price < 50:
            add_qty = round(10 / market_price)
            info(f"PoloniexTrader: buying {add_qty:.1f} additional TRX tokens")
            self.api.buy("USDT_TRX", market_price*1.01, add_qty, {'fillOrKill': True})
            new_qty = float(self.api.returnBalances()['TRX'])
            if new_qty < add_qty:
                warn("PoloniexTrader: failed to buy TRX tokens")
