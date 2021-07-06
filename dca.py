import json, datetime, argparse
from trader_factory import TraderFactory
from market_price import MarketPrice
from trader import Trader
from pandas.core.frame import DataFrame
from termcolor import cprint
import dca_settings as ds



def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])

def err(msg: str):
    cprint(f"error: {msg}", 'red')

def msg_accumulate(coin: str):
    cprint(f"buying : {coin}", 'green')

coins_auto_accumulate = [c for c in ds.coin_ids if c not in ds.auto_accumulate_black_list]

def create_trader(coin: str) -> Trader:
    return TraderFactory.create_trader(coin, ds.coin_exchg[coin] if coin in ds.coin_exchg.keys() else "dummy")

def get_quota(coin: str):
    mult = ds.quota_multiplier[coin] if coin in ds.quota_multiplier.keys() else 1
    return ds.quota_usd * mult

def pretty_json(s):
    print(json.dumps(s, indent=4, sort_keys=True))

def weight_function(base_price: float, price: float):
    return base_price/price


class TradeHelper:
    def __init__(self):
        self.market_price = MarketPrice(ds.coin_ids+list(ds.liquidity_pairs.values()))

    def get_market_price(self, coin: str) -> float:
        return self.market_price.get_market_price(coin)

    def get_qty_weight(self, coin: str) -> float:
        return weight_function(ds.base_price[coin], self.get_market_price(coin))


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
        # returns list [ ( [+-]coin_qty, price ) ]
        #
        cur = self.con.cursor()
        trades = list()
        for row in cur.execute(f"SELECT qty,price FROM dca WHERE sym = '{sym}' ORDER BY date"):
            entry =(row[0], row[1], )
            trades.append(entry)
        #print(trades)
        return trades


def accumulate(qty: float, coins: list[str], dry_run: bool):
    th = TradeHelper()
    db = Db()
    a= list()
    for coin in coins:

        msg_accumulate(coin)

        try:
            coin_has_liquidity_pair = coin in ds.liquidity_pairs.keys()

        quota_coin = get_quota(coin) if not qty else qty
        qty_factor = th.get_qty_weight(coin)
        daily_qty = round(quota_coin * qty_factor)
            # if coin_has_liquidity_pair:
            #     daily_qty = daily_qty / 2

        trader: Trader = create_trader(coin)
        if trader:
            if dry_run:
                actual_price = th.get_market_price(coin)
            else:
                actual_price, coin_qty = trader.buy_market(daily_qty)
            a.append({
                'coin': coin,
                'price': actual_price,
                'qty_factor': qty_factor,
                'usd': coin_qty*actual_price,
                'coins': coin_qty,
            })
            if not dry_run:
                db.add(coin, coin_qty, actual_price)

        # if coin has an associated liquidity pair coin,  buy exactly same USD qty of the paired coin
        if coin_has_liquidity_pair:
                coin2 = ds.liquidity_pairs[coin]
            trader: Trader = create_trader(coin2)
            if trader:
                if dry_run:
                    actual_price2 = th.get_market_price(coin2)
                else:
                    actual_price2, coin_qty2 = trader.buy_market(daily_qty)
                a.append({
                    'coin': coin2,
                    'price': actual_price2,
                    'qty_factor': 1,
                    'usd': coin_qty2*actual_price2,
                    'coins': coin_qty2,
                })
                if not dry_run:
                    db.add(coin2, coin_qty2, actual_price2)
        except Exception as e:
            err(f"coin={coin} exc={str(e)}")

    if len(a):
        df = DataFrame.from_dict(a)
        print(df.to_string(index=False))
    else:
        print('nothing was added.')


def stats():
    th = TradeHelper()
    db = Db()
    syms = db.get_syms()
    stats_data = list()
    for coin in syms:
        trades = db.get_sym_trades(coin)

        buys = list()
        sells = list()
        for i in trades:
            if i[0] < 0:
                sells.append((-i[0], i[1],))
            else:
                buys.append(i)
        total_buys_value = sum( [ x[0] * x[1] for x in buys] )
        total_buys_qty = sum( [ x[0] for x in buys] )
        total_sells_value = sum( [ x[0] * x[1] for x in sells] )
        total_sells_qty = sum( [ x[0] for x in sells] )

        unrealized_sells_value = (total_buys_qty - total_sells_qty) * th.get_market_price(coin)
        pnl = total_sells_value + unrealized_sells_value - total_buys_value
        pnl_percent = round(pnl / total_buys_value * 100, 1)

        stats_data.append({
            'coin': coin,
            'total_buys_value': total_buys_value,
            'total_buys_qty': total_buys_qty,
            'total_sells_value': total_sells_value,
            'total_sells_qty': total_sells_qty,
            'unrealized_sells_value': unrealized_sells_value,
            'pnl': pnl,
            'pnl %': pnl_percent,
        })
    title("PnL")
    df_pnl = DataFrame.from_dict(stats_data)
    df_pnl = df_pnl.sort_values('pnl %', ascending=False)
    print(df_pnl.to_string(index=False,formatters={'total_buys_qty':lambda x: f'{x:8.8f}'}))
    title("Portfolio Structure")
    df_pf_structure = df_pnl
    df_pf_structure['%'] = round(df_pf_structure['unrealized_sells_value'] / sum(df_pf_structure['unrealized_sells_value']) * 100, 1)
    df_pf_structure = df_pf_structure.sort_values('%', ascending=False)
    print(df_pf_structure.to_string(index=False, columns=['coin', '%']))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry', action='store_const', const='True',  help='Just print actions, do not write to database or buy anything')
    parser.add_argument('--add', action='store_const', const='True',  help='Accumulate positions')
    parser.add_argument('--coin', nargs=1, type=str,  help='Used with --add. Only add position for specified coin')
    parser.add_argument('--stats', action='store_const', const='True', help='Print average buy price of all positions')
    parser.add_argument('--qty', nargs=1, type=int, help='Quota in USD for every position')
    args = parser.parse_args()

    if args.add:
        accumulate(qty=args.qty[0] if args.qty else None, coins=args.coin if args.coin else coins_auto_accumulate, dry_run=args.dry)
    if args.stats:
        stats()


if __name__ == '__main__':
    main()
