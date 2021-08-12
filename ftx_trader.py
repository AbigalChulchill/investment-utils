from trader import Trader
import ftx_api, ftx_config
import time

sym_to_market={
    'ftx-token':       'FTT/USD',
    'solana':          'SOL/USD',
    'bitcoin':         'WBTC/USD',
}

class FtxTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_market.keys()


    def __init__(self, sym: str):
        self.market = sym_to_market[sym]
        self.api = ftx_api.Ftx(ftx_config.API_KEY, ftx_config.SECRET, ftx_config.SUBACCOUNT)


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

