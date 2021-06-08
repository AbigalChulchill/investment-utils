import json, datetime, argparse, pycoingecko
from trader_factory import TraderFactory
from trader import Trader
from pandas.core.frame import DataFrame


coin_ids=[
    "bitcoin",
    "dogecoin",
    "binancecoin",
    "ethereum",
    "matic-network"
]


base_price ={
    "bitcoin": 15000,
    "ethereum": 600,
    "matic-network": 0.3,
    "binancecoin": 50,
    "dogecoin": 0.05
}


quota_usd = 50

liquidity_pairs = {
    "ethereum": "polyzap",
    "matic-network": "polyzap",
    "binancecoin": "lien",
}

def get_quota(coin: str):
    return quota_usd

def pretty_json(s):
    print(json.dumps(s, indent=4, sort_keys=True))

def weight_function(base_price: float, price: float):
    return base_price/price


class TradeHelper:
    def __init__(self):
        cg = pycoingecko.CoinGeckoAPI()
        self.price_data = cg.get_price(ids=coin_ids+list(liquidity_pairs.values()), vs_currencies='usd')

    def get_current_price(self, coin: str) -> float:
        return float(self.price_data[coin]['usd'])

    def get_qty_weight(self, coin: str) -> float:
        return weight_function(base_price[coin], self.get_current_price(coin))


class Db:
    def __init__(self):
        import sqlite3
        self.con = sqlite3.connect('dca.db')
        cur = self.con.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS dca (date text, sym text, qty real, price real)''')
        self.con.commit()

    def add(self, sym: str, qty: float, price: float ):
        cur = self.con.cursor()
        now = datetime.datetime.now()
        cur.execute("INSERT INTO dca VALUES (?,?,?,?)", (now, sym, qty, price))
        self.con.commit()

    def get_syms(self) -> list:
        cur = self.con.cursor()
        syms = list()
        for row in cur.execute(f"SELECT sym FROM dca"):
            syms.append(row[0])
        return set(syms)


    def get_sym_trades(self, sym: str) -> tuple:
        #
        # tuple(list(qty_usd), list(qty_coin))
        #
        cur = self.con.cursor()
        qty_usd = list()
        qty_coin = list()
        for row in cur.execute(f"SELECT qty,price FROM dca WHERE sym = '{sym}'"):
            qty_usd.append(row[0])
            qty_coin.append(row[0]/row[1])
        #print(trades)
        return (qty_usd,qty_coin,)


def accumulate(qty: float):
    th = TradeHelper()
    db = Db()
    a= list()
    for coin in coin_ids:

        coin_has_liquidity_pair = coin in liquidity_pairs.keys()

        quota_coin = get_quota(coin) if not qty else qty
        qty_factor = th.get_qty_weight(coin)
        daily_qty = round(quota_coin * qty_factor)
        if coin_has_liquidity_pair:
            daily_qty = daily_qty / 2

        trader: Trader = TraderFactory.create_trader(coin)
        if trader:
            actual_price = trader.buy_market(daily_qty)
            a.append({
                'coin': coin,
                'price': actual_price,
                'qty_factor': qty_factor,
                'daily_qty': daily_qty,
            })
            db.add(coin, daily_qty, actual_price)

        # if coin has an associated liquidity pair coin,  buy exactly same USD qty of the paired coin
        if coin_has_liquidity_pair:
            coin2 = liquidity_pairs[coin]
            trader: Trader = TraderFactory.create_trader(coin2)
            if trader:
                actual_price2 = trader.buy_market(daily_qty)
                a.append({
                    'coin': coin2,
                    'price': actual_price2,
                    'qty_factor': 1,
                    'daily_qty': daily_qty,
                })
                db.add(coin2, daily_qty, actual_price2)
    df = DataFrame.from_dict(a)
    print(df.to_string(index=False))


def stats():
    th = TradeHelper()
    db = Db()
    syms = db.get_syms()
    a= list()
    for coin in syms:
        qty_usd_list, qty_coin_list = db.get_sym_trades(coin)
        sum_qty_usd = sum(qty_usd_list)
        sum_qty_coin = sum(qty_coin_list)
        avg_price  = sum_qty_usd / sum_qty_coin
        pnl = (th.get_current_price(coin) - avg_price) / avg_price
        a.append({
            'coin': coin,
            'sum_qty_usd': sum_qty_usd,
            'sum_qty_coin': sum_qty_coin,
            'avg_price': avg_price,
            'pnl': pnl,
        })
    df = DataFrame.from_dict(a)
    print(df.to_string(index=False))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--add', action='store_const', const='True',  help='Accumulate positions')
    parser.add_argument('--stats', action='store_const', const='True', help='Print average buy price of all positions')
    parser.add_argument('--qty', nargs=1, type=int, help='Quota in USD for every position')
    args = parser.parse_args()

    if args.add:
        accumulate(args.qty[0] if args.qty else None)
    if args.stats:
        stats()


if __name__ == '__main__':
    main()
