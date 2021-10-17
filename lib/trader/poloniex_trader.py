import time, traceback
from lib.common.msg import info, warn
from lib.common.id_map_poloniex import id_to_poloniex
from lib.trader import poloniex_api
from lib.trader.trader import Trader


MAX_RETRIES = 3
DELAY = 5

class PoloniexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in id_to_poloniex.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self.pair = id_to_poloniex[sym]
        self.api = poloniex_api.Poloniex(api_key, secret)

    def buy_market(self, qty_usd: float) -> float:
        self._check_trx_balance()
        retries = MAX_RETRIES
        while retries >= 0:
            try:
                return self._buy_market(qty_usd)
            except Exception:
                if retries > 0:
                    retries -= 1
                    traceback.print_exc()
                    warn(f"PoloniexTrader: buy: failed, retrying in {DELAY} seconds...")
                    time.sleep(DELAY)
                else:
                    raise

    def sell_market(self, qty_tokens: float) -> float:
        self._check_trx_balance()
        retries = MAX_RETRIES
        while retries >= 0:
            try:
                return self._sell_market(qty_tokens)
            except Exception:
                if retries > 0:
                    retries -= 1
                    traceback.print_exc()
                    warn(f"PoloniexTrader: sell: failed, retrying in {DELAY} seconds...")
                    time.sleep(DELAY)
                else:
                    raise

    def _handle_trade(self, response: dict):
        try:
            trades = response['resultingTrades']
        except:
            print(f"response : {response}")
            raise
        else:
            total_qty_coin = sum( [float(x['amount']) for x in trades] )
            total_qty_usd = sum( [float(x['total']) for x in trades] )
            fill_price = total_qty_usd / total_qty_coin
            return [fill_price, total_qty_coin]

    def _buy_market(self, qty_usd: float) -> float:
        market_price = float(self.api.returnOrderBook(self.pair)['asks'][1][0])
        response = self.api.buy(self.pair, market_price, qty_usd / market_price, {'fillOrKill': True})
        return self._handle_trade(response)

    def _sell_market(self, qty_tokens: float) -> float:
        market_price = float(self.api.returnOrderBook(self.pair)['bids'][1][0])
        response = self.api.sell(self.pair, market_price, qty_tokens, {'fillOrKill': True})
        return self._handle_trade(response)

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
