from trader import Trader
import poloniex_api, poloniex_config

sym_to_pair={
    'bitcoin':          'USDT_BTC',
    'dogecoin':         'USDT_DOGE',
    'ethereum':         'USDT_ETH',
    'matic-network':    'USDT_MATIC',
    'ripple':           'USDT_XRP',
    'gitcoin':          'USDT_GTC',
    'shiba-inu':        'USDT_SHIB',
}

class PoloniexTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_pair.keys()


    def __init__(self, sym: str):
        self.pair = sym_to_pair[sym]
        self.api = poloniex_api.Poloniex(poloniex_config.API_KEY, poloniex_config.SECRET)


    def buy_market(self, qty_usd: float) -> float:
        market_price = float(self.api.returnTicker(self.pair))
        response = self.api.buy(self.pair, market_price*1.01, qty_usd / market_price, {'fillOrKill': True})
        trades = response['resultingTrades']
        total_qty_coin = sum( [float(x['amount']) for x in trades] )
        total_qty_usd = sum( [float(x['total']) for x in trades] )
        fill_price = total_qty_usd / total_qty_coin
        #print(f'fill price {fill_price}, market price {market_price}')
        return fill_price
