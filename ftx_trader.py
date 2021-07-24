from trader import Trader
import ftx_api, ftx_config

sym_to_market={
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
        response = self.api.place_order(market=self.market, side="buy", price=0, limit_or_market="market", size= qty_usd / market_price, ioc=True)
        #fill_price = float(response['price'])
        fill_price = market_price
        return [fill_price, float(response['size'])]
