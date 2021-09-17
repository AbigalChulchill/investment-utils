import time
from . import ftx_api
from .trader import Trader

sym_to_market={
    #crypto
    'ftx-token':       'FTT/USD',
    'solana':          'SOL/USD',
    'bitcoin':         'WBTC/USD',
    'enjincoin':       'ENJ/USD',
    'fantom':          'FTM/USD',

    #stocks
    '#AAPL':  'AAPL/USD',
    '#AMZN':  'AMZN/USD',
    '#BABA':  'BABA/USD',
    '#BILI':  'BILI/USD',
    '#COIN':  'COIN/USD',
    '#FB':    'FB/USD',
    '#GBTC':  'GBTC/USD',
    '#GOOGL': 'GOOGL/USD',
    '#MSTR':  'MSTR/USD',
    '#NIO':   'NIO/USD',
    '#PYPL':  'PYPL/USD',
    '#TSLA':  'TSLA/USD',
    '#TWTR':  'TWTR/USD',
}


class FtxTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_market.keys()


    def __init__(self, sym: str, api_key: str, secret: str, subaccount: str):
        self.market = sym_to_market[sym]
        self.api = ftx_api.Ftx(api_key, secret, subaccount)

    def buy_market(self, qty_usd: float) -> float:
        market_price = self.api.get_orderbook(self.market)['asks'][0][0]
        order_id = self.api.place_order(market=self.market, side="buy", price=0, limit_or_market="market", size= qty_usd / market_price, ioc=False)
        retries = 5
        while retries > 0:
            time.sleep(1)
            response = self.api.get_order_status(order_id)
            fill_qty = float(response['filledSize'])
            req_qty = float(response['size'])
            fill_price  = float(response['avgFillPrice'])
            if (fill_qty - req_qty) < 0.001:
                return [fill_price, fill_qty]
            retries = retries - 1
        raise Exception("not filled")

    def sell_market(self, qty_tokens: float) -> float:
        market_price = self.api.get_orderbook(self.market)['bids'][0][0]
        order_id = self.api.place_order(market=self.market, side="sell", price=0, limit_or_market="market", size=qty_tokens, ioc=False)
        retries = 5
        while retries > 0:
            time.sleep(1)
            response = self.api.get_order_status(order_id)
            fill_qty = float(response['filledSize'])
            req_qty = float(response['size'])
            fill_price  = float(response['avgFillPrice'])
            if (fill_qty - req_qty) < 0.001:
                return [fill_price, fill_qty]
            retries = retries - 1
        raise Exception("not filled")

