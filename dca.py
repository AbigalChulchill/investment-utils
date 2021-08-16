import os, json, datetime, argparse, re, yaml, time
from trader_factory import TraderFactory
from market_data import MarketData
from trader import Trader
from pnl import calculate_pnl
from pandas.core.frame import DataFrame
from termcolor import cprint

ds = dict()


def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])

def err(msg: str):
    cprint(f"error: {msg}", 'red')

def warn(msg: str):
    cprint(f"warning: {msg}", 'yellow')

def msg_accumulate(coin: str):
    cprint(f"buying : {coin}", 'green')

def msg_remove(coin: str):
    cprint(f"selling : {coin}", 'green')


def create_trader(coin: str) -> Trader:
    return TraderFactory.create_trader(coin, ds['coin_exchg'][coin] if coin in ds['coin_exchg'].keys() else "dummy")

def create_dummy_trader(coin: str) -> Trader:
    return TraderFactory.create_trader(coin, "dummy")


def get_quota(coin: str):
    #mult = ds['quota_multiplier'][coin] if coin in ds['quota_multiplier'].keys() else 1
    return ds['quota_usd']# * mult

def pretty_json(s):
    print(json.dumps(s, indent=4, sort_keys=True))


class TradeHelper:
    def __init__(self):
        self.market_data = MarketData(ds['coin_ids'])

    def get_market_price(self, coin: str) -> float:
        return self.market_data.get_market_price(coin)

    def get_market_cap(self, coin: str) -> float:
        return self.market_data.get_norm_market_cap(coin)


class Db:
    def __init__(self):
        import sqlite3
        self.con = sqlite3.connect('dca.db')
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
        return set(syms)

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



def accumulate(qty: float, coins: list[str]):
    th = TradeHelper()
    db = Db()
    a= list()
    for coin in coins:

        msg_accumulate(coin)

        try:
            qty_factor = 1
            if qty:
                daily_qty = qty
            else:
                quota_coin = get_quota(coin)
                avg_price_last_n_trades = db.get_sym_average_price_n_last_trades(coin, ds['qty_factor_average_days'])
                current_price = th.get_market_price(coin)
                if avg_price_last_n_trades:
                    r = abs(current_price - avg_price_last_n_trades) / current_price
                    if current_price > avg_price_last_n_trades:
                        qty_factor = max(1 - ds['qty_factor_max_deviation'], 1 - r)
                    else:
                        qty_factor = min(1 + ds['qty_factor_max_deviation'], 1 + r)
                daily_qty = round(quota_coin * qty_factor)

            trader: Trader = create_trader(coin)
            if trader:
                actual_price, coin_qty = trader.buy_market(daily_qty)
                a.append({
                    'coin': coin,
                    'price': actual_price,
                    'qty_factor': qty_factor,
                    'usd': coin_qty*actual_price,
                    'coins': coin_qty,
                })
                db.add(coin, coin_qty, actual_price)
        except Exception as e:
            err(f"{coin} : was not added, exc was '{str(e)}'")

    if len(a):
        df = DataFrame.from_dict(a)
        print(df.to_string(index=False))
    else:
        print('nothing was added.')


def remove(coin: str, qty: str):
    th = TradeHelper()
    db = Db()
    a= list()

    msg_remove(coin)

    total_buy_value,total_buy_qty,total_sell_value,total_sell_qty = db.get_sym_cumulative_trades(coin)
    available_sell_qty = total_buy_qty - total_sell_qty
    actual_sell_qty = 0
    m = re.match(r"([0-9]+)%", qty)
    if m:
        actual_sell_qty = available_sell_qty * float(m[1]) / 100
    else:
        actual_sell_qty = min(available_sell_qty, float(qty))

    trader: Trader = create_trader(coin)
    if trader:
        actual_price, actual_qty = trader.sell_market(actual_sell_qty)
        a.append({
            'coin': coin,
            'price': actual_price,
            'coins sold': actual_qty,
            'usd sold': actual_qty*actual_price,
            'coins avail': available_sell_qty - actual_qty,
            'usd avail': (available_sell_qty - actual_qty)*actual_price,
        })
        db.remove(coin, actual_qty, actual_price)

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
    th = TradeHelper()
    db = Db()
    syms = db.get_syms()
    stats_data = list()
    for coin in syms:
        total_buy_value,total_buy_qty,total_sell_value,total_sell_qty = db.get_sym_cumulative_trades(coin)

        market_price = th.get_market_price(coin)
        pnl_data = calculate_pnl(total_buy_value, total_buy_qty, total_sell_value, total_sell_qty, market_price)

        stats_data.append({
            'coin': coin,
            'buy_value': total_buy_value,
            'buy_qty': total_buy_qty,
            'average_price': total_buy_value / total_buy_qty,
            'current_price': market_price,
            'sell_value': total_sell_value,
            'sell_qty': total_sell_qty,
            'available_qty': total_buy_qty - total_sell_qty,
            'unrealized_sell_value': pnl_data.unrealized_sell_value,
            'r pnl': pnl_data.realized_pnl,
            'r pnl %': pnl_data.realized_pnl_percent,
            'u pnl': pnl_data.unrealized_pnl,
            'u pnl %': pnl_data.unrealized_pnl_percent,
        })
    title("PnL")
    df_pnl = DataFrame.from_dict(stats_data)
    df_pnl = df_pnl.sort_values('u pnl %', ascending=False)
    columns=["coin", "average_price", "current_price", "u pnl %"] if hide_private_data else None
    print(df_pnl.to_string(index=False,formatters={'buy_qty':lambda x: f'{x:8.8f}', 'available_qty':lambda x: f'{x:8.8f}'},columns=columns))
    title("Portfolio Structure")
    df_pf_structure = df_pnl
    df_pf_structure['%'] = round(df_pf_structure['unrealized_sell_value'] / sum(df_pf_structure['unrealized_sell_value']) * 100, 1)
    df_pf_structure = df_pf_structure.sort_values('%', ascending=False)
    print(df_pf_structure.to_string(index=False, columns=['coin', '%']))


def read_settings() -> dict:
    ds =dict ()
    with open('dca_settings_default.yml', 'r') as file:
        ds = yaml.safe_load(file)

    if os.path.exists('dca_settings_override.yml'):
        with open('dca_settings_override.yml', 'r') as file:
            ds = ds | yaml.safe_load(file)
    return ds


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
    args = parser.parse_args()

    if args.add:
        coins_auto_accumulate = [c for c in ds['coin_ids'] if c not in ds['auto_accumulate_black_list']]
        accumulate(qty=args.qty[0] if args.qty else None, coins=args.coin if args.coin else coins_auto_accumulate)
    elif args.remove:
        if args.coin:
            remove(coin=args.coin[0], qty=args.remove[0])
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
