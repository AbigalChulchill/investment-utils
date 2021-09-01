import json, datetime, argparse, re, yaml, traceback
from pandas.core.frame import DataFrame
from termcolor import cprint
from typing import List

from lib.trader.trader_factory import TraderFactory
from lib.trader.trader import Trader
from lib.common.market_data import MarketData
from lib.common import pnl
from lib.common.msg import err, warn


ds = dict()

def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])

def msg_accumulate(coin: str):
    cprint(f"buying : {coin}", 'green')

def msg_remove(coin: str):
    cprint(f"selling : {coin}", 'green')

def create_trader(coin: str) -> Trader:
    return TraderFactory.create_dca(coin, ds['coin_exchg'][coin])

def create_dummy_trader(coin: str) -> Trader:
    return TraderFactory.create_dummy(coin)

def get_quota_fixed_multiplier(coin: str):
    param = 'quota_fixed_multiplier'
    if param in ds.keys():
        if coin in ds[param].keys():
            return ds[param][coin]
    return 1

def get_quota(coin: str):
    return ds['quota_usd'] * get_quota_fixed_multiplier(coin)

def pretty_json(s):
    print(json.dumps(s, indent=4, sort_keys=True))


class TradeHelper:
    def __init__(self, ids: list):
        self.market_data = MarketData(list(set(ids + list(ds['coin_exchg'].keys()))))

    def get_market_price(self, coin: str) -> float:
        return self.market_data.get_market_price(coin)

    def get_24h_change(self, coin: str) -> float:
        return self.market_data.get_24h_change(coin)

    def get_avg_price_n_days(self, coin: str, days_before: int) -> float:
        return self.market_data.get_avg_price_n_days(coin, days_before)

class Db:
    def __init__(self):
        import sqlite3
        self.con = sqlite3.connect('config/dca.db')
        self.con.execute('''CREATE TABLE IF NOT EXISTS dca (date text, sym text, qty real, price real)''')
        self.con.commit()

    def add(self, sym: str, qty: float, price: float ):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (now, sym, qty, price))
        self.con.commit()

    def remove(self, sym: str, qty: float, price: float ):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (now, sym, -qty, price))
        self.con.commit()

    def burn(self, sym: str, qty: float):
        now = datetime.datetime.now()
        self.con.execute("INSERT INTO dca VALUES (?,?,?,?)", (now, sym, -qty, 0))
        self.con.commit()

    def delete_all(self, sym: str):
        self.con.execute("DELETE FROM dca WHERE sym = ?", (sym,))
        self.con.commit()

    def get_syms(self) -> list:
        syms = list()
        for row in self.con.execute(f"SELECT sym FROM dca"):
            syms.append(row[0])
        return list(set(syms))

    def _get_sym_trades(self, sym: str) -> tuple:
        #
        # returns list [ ( [+-]coin_qty, price ) ]
        #
        trades = list()
        for row in self.con.execute(f"SELECT qty,price FROM dca WHERE sym = '{sym}' ORDER BY date"):
            entry =(row[0], row[1], )
            trades.append(entry)
        #print(trades)
        return trades

    def get_sym_cumulative_trades(self, sym:str) -> tuple:
        trades = self._get_sym_trades(sym)

        buys = list()
        sells = list()
        for i in trades:
            if i[0] < 0:
                sells.append((-i[0], i[1],))
            else:
                buys.append(i)

        total_buy_value = sum( [ x[0] * x[1] for x in buys] )
        total_buy_qty = sum( [ x[0] for x in buys] )
        total_sell_value = sum( [ x[0] * x[1] for x in sells] )
        total_sell_qty = sum( [ x[0] for x in sells] )
        return total_buy_value,total_buy_qty,total_sell_value,total_sell_qty

    def get_sym_available_qty(self, sym:str) -> float:
        trades = self._get_sym_trades(sym)
        return sum([i[0] for i in trades])

    def get_sym_trades_for_pnl(self, sym:str) -> List[pnl.Order]:
        trades = self._get_sym_trades(sym)
        orders = []
        for i in trades:
            if i[0] < 0:
                orders.append(pnl.Order("SELL", -i[0]*i[1], -i[0]))
            else:
                orders.append(pnl.Order("BUY", i[0]*i[1], i[0]))
        return orders

    def get_sym_average_price_n_last_trades(self, sym:str, n: int) -> float:
        trades = self._get_sym_trades(sym)
        buys = [x for x in trades if x[0] > 0]
        n = min(n, len(buys))
        if n > 0:
            avg_price = sum([x[1] for x in buys[-n:]]) / n
        else:
            avg_price = None
        #print(f"sym {sym} avgprice {n} = {avg_price}")
        return avg_price



def accumulate(qty: float, coins: list[str], dry: bool):
    db = Db()
    th = TradeHelper(db.get_syms())
    a= list()
    for coin in coins:

        msg_accumulate(coin)

        try:
            quota_mul = 1
            if qty:
                daily_qty = qty
            else:
                quota_coin = get_quota(coin)
                current_price = th.get_market_price(coin)
                try: # get_avg_price_n_days might fail if the asset is not known by Binance. 
                avg_price_last_n_days = th.get_avg_price_n_days(coin, ds['quota_multiplier_average_days'])
                    quota_mul = avg_price_last_n_days / current_price
                except:
                    warn(f"average price data on {coin} is not available, using default quota_mul")
                quota_mul = min(quota_mul, ds['quota_multiplier_max'])
                daily_qty = round(quota_coin * quota_mul)

            trader: Trader = create_trader(coin)
            if trader:
                if dry:
                    actual_price = th.get_market_price(coin)
                    coin_qty = daily_qty / actual_price
                else:
                    actual_price, coin_qty = trader.buy_market(daily_qty)
                    db.add(coin, coin_qty, actual_price)
                a.append({
                    'coin': coin,
                    'price': actual_price,
                    'quota_mul': round(quota_mul,2),
                    'usd': coin_qty*actual_price,
                    'coins': coin_qty,
                })
        except Exception as e:
            err(f"{coin} : was not added")
            traceback.print_exc()

    if len(a):
        df = DataFrame.from_dict(a)
        print(df.to_string(index=False))
    else:
        print('nothing was added.')


def remove(coin: str, qty: str, dry: bool):
    db = Db()
    th = TradeHelper(db.get_syms())
    a= list()

    msg_remove(coin)

    market_price = th.get_market_price(coin)
    available_sell_qty = db.get_sym_available_qty(coin)
    sell_qty = 0
    m = re.match(r"([0-9]+)%", qty)
    if m:
        sell_qty = available_sell_qty * float(m[1]) / 100
    else:
        sell_qty = min(available_sell_qty, float(qty) / market_price)

    trader: Trader = create_trader(coin)
    if trader:
        if dry:
            actual_price = th.get_market_price(coin)
            actual_qty = sell_qty
        else:
            actual_price, actual_qty = trader.sell_market(sell_qty)
            db.remove(coin, actual_qty, actual_price)
        a.append({
            'coin': coin,
            'price': actual_price,
            'coins sold': actual_qty,
            'usd sold': actual_qty*actual_price,
            'coins avail': available_sell_qty - actual_qty,
            'usd avail': (available_sell_qty - actual_qty)*actual_price,
        })

    if len(a):
        df = DataFrame.from_dict(a)
        print(df.to_string(index=False))
    else:
        print('not removed.')


def burn(coin: str, qty: float):
    db = Db()
    db.burn(coin, qty)
    print(f"burned {qty} {coin}")


def close(coin: str):
    db = Db()
    db.delete_all(coin)
    print(f"{coin} position has been closed")


def stats(hide_private_data: bool):
    db = Db()
    th = TradeHelper(db.get_syms())
    syms = db.get_syms()
    stats_data = list()
    for coin in syms:

        market_price = th.get_market_price(coin)
        available_qty = db.get_sym_available_qty(coin)
        pnl_data = pnl.calculate_inc_pnl(db.get_sym_trades_for_pnl(coin), market_price)

        stats_data.append({
            'coin': coin,
            'available_qty': available_qty,
            'break_even_price': pnl_data.break_even_price,
            'current_price': market_price,
            '24h chg %': round(th.get_24h_change(coin),1),
            'unrealized_sell_value': round(pnl_data.unrealized_sell_value,1),
            'r pnl': round(pnl_data.realized_pnl,1),
            'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
            'u pnl': round(pnl_data.unrealized_pnl,1),
            'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
        })
    title("PnL")
    df_pnl = DataFrame.from_dict(stats_data)
    df_pnl = df_pnl.sort_values('u pnl %', ascending=False)
    columns=["coin", "break_even_price", "current_price", "u pnl %"] if hide_private_data else None
    formatters={
        'buy_qty':          lambda x: f'{x:8.8f}',
        'available_qty':    lambda x: f'{x:8.8f}',
    }
    print(df_pnl.to_string(index=False,formatters=formatters,columns=columns))
    title("Portfolio Structure")
    df_pf_structure = df_pnl
    df_pf_structure['%'] = round(df_pf_structure['unrealized_sell_value'] / sum(df_pf_structure['unrealized_sell_value']) * 100, 1)
    df_pf_structure = df_pf_structure.sort_values('%', ascending=False)
    print(df_pf_structure.to_string(index=False, columns=['coin', '%']))


def read_settings() -> dict:
    with open('config/dca.yml', 'r') as file:
        return yaml.safe_load(file)


def main():
    global ds
    ds = read_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument('--add', action='store_const', const='True',  help='Accumulate positions')
    parser.add_argument('--remove', nargs=1, type=str,  help='Partially remove from a position. Arg: amount or %% of coins to remove. Requires --coin')
    parser.add_argument('--burn', nargs=1, type=float, help='Remove coins from equity without selling (as if lost, in other circumstances). Requires --coin')
    parser.add_argument('--close', action='store_const', const='True',  help='Close position. Requires --coin')
    parser.add_argument('--qty', nargs=1, type=int, help='Quota in USD for every position')
    parser.add_argument('--coin', nargs=1, type=str,  help='Perform an action on the specified coin only, used with --add, --remove and --close')
    parser.add_argument('--stats', action='store_const', const='True', help='Print average buy price of all positions')
    parser.add_argument('--hide-private-data', action='store_const', const='True', help='Do not include private data in the --stat output')
    parser.add_argument('--dry', action='store_const', const='True', help='Dry run: do not actually buy or sell, just report on what will be done')
    args = parser.parse_args()

    if args.add:
        accumulate(qty=args.qty[0] if args.qty else None, coins=args.coin if args.coin else ds['auto_accumulate_list'], dry=args.dry)
    elif args.remove:
        if args.coin:
            remove(coin=args.coin[0], qty=args.remove[0], dry=args.dry)
        else:
            print("remove: requires --coin")
    elif args.close:
        if args.coin:
            close(coin=args.coin[0])
        else:
            print("close: requires --coin")
    elif args.burn:
        if args.coin:
            burn(coin=args.coin[0], qty=args.burn[0])
        else:
            print("burn: requires --coin")
    elif args.stats:
        stats(args.hide_private_data)


if __name__ == '__main__':
    main()
