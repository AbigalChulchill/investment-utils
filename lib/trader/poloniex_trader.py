import time, traceback
from lib.common.msg import warn
from . import poloniex_api
from .trader import Trader

sym_to_pair={
    'bitcoin':          'USDT_BTC',
    'dogecoin':         'USDT_DOGE',
    'ethereum':         'USDT_ETH',
    'matic-network':    'USDT_MATIC',
    'ripple':           'USDT_XRP',
    'cardano':          'USDT_ADA',
    'gitcoin':          'USDT_GTC',
    'shiba-inu':        'USDT_SHIB',
    "curve-dao-token":  "USDT_CRV",
    "aave":             "USDT_AAVE",
    "0x":               "USDT_ZRX",
    "havven":           "USDT_SNX",
    "ethereum-classic": "USDT_ETC",
    "polkadot":         "USDT_DOT",
    'basic-attention-token': 'USDT_BAT',
}

MAX_RETRIES = 3
DELAY = 5

class PoloniexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_pair.keys()

    def __init__(self, sym: str, api_key: str, secret: str):
        self.pair = sym_to_pair[sym]
        self.api = poloniex_api.Poloniex(api_key, secret)

    def buy_market(self, qty_usd: float) -> float:
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
