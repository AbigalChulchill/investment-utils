from trader import Trader
import binance_api, binance_config

sym_to_pair={
    'gitcoin':              'GTCUSDT',
    'decentraland':         'MANAUSDT',
    'pancakeswap-token':    'CAKEUSDT',
}
sym_round_decimals={
    'gitcoin':              2,
    'decentraland':         2,
    'pancakeswap-token':    2,
}

class BinanceTrader(Trader):

    @staticmethod
    def handles_sym(sym: str) -> bool:
        return sym in sym_to_pair.keys()


    def __init__(self, sym: str):
        self.pair = sym_to_pair[sym]
        self.round_decimals = sym_round_decimals[sym]
        self.api = binance_api.Binance(binance_config.API_KEY, binance_config.SECRET)


    def buy_market(self, qty_usd: float) -> float:
        market_price = float(self.api.get_orderbook(symbol=self.pair)['asks'][0][0])
        qty_coin = round(qty_usd / market_price,self.round_decimals)
        #print(f"qty_usd={qty_usd} qty_coin={qty_coin} market_price={market_price}")
        response = self.api.buy_market(symbol=self.pair, quantity=qty_coin)
        trades = response['fills']
        total_qty_coin = sum( [float(x['qty']) for x in trades] )
        total_qty_usd = sum( [float(x['qty'])*float(x['price']) for x in trades] )
        fill_price = total_qty_usd / total_qty_coin
        return [fill_price, total_qty_coin]
