import json, datetime, argparse, re, yaml, traceback, math
from pandas.core.frame import DataFrame
from termcolor import cprint
from typing import List, Tuple

from lib.trader.trader_factory import TraderFactory
from lib.trader.trader import Trader
from lib.common.market_data import MarketData
from lib.common import accounts_balance
from lib.common import pnl
from lib.common.msg import err, warn
from lib.common.misc import is_stock


ds = dict()

def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])

def title2(name: str):
    cprint(f"  {name}", 'white', attrs=['bold'])

def msg_buying(coin: str):
    print("buying : ", end="")
    cprint(coin, "green")

def msg_selling(coin: str):
    print("selling : ", end="")
    cprint(coin, "green")

def create_trader(coin: str) -> Trader:
    return TraderFactory.create_dca(coin, ds['asset_exchg'][coin])

def create_dummy_trader(coin: str) -> Trader:
    return TraderFactory.create_dummy(coin)

def get_quota_fixed_multiplier(coin: str):
    param = 'quota_fixed_multiplier'
    if param in ds.keys():
        if coin in ds[param].keys():
            return ds[param][coin]
    return 1


class TradeHelper:
    def __init__(self, ids: list):
        self.market_data = MarketData(list(set(ids + list(ds['asset_exchg'].keys()))))

    def get_market_price(self, coin: str) -> float:
        return self.market_data.get_market_price(coin)

    def is_tradeable(self, asset: str) -> bool:
        return self.market_data.is_tradeable(asset)

    def get_daily_change(self, coin: str) -> float:
        return self.market_data.get_daily_change(coin)

    def get_avg_price_n_days(self, coin: str, days_before: int) -> float:
        return self.market_data.get_avg_price_n_days(coin, days_before)

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        return self.market_data.get_distance_to_avg_percent(coin, days_before)

    def is_dipping(self, coin: str) -> float:
        return self.market_data.is_dipping(coin)

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


def print_account_balances():
    title("Account Balances, USD")
    df_balances = DataFrame.from_dict(accounts_balance.get_available_usd_balances_dca())
    print(df_balances.to_string(index=False))


def calc_daily_qty(asset: str, th: TradeHelper, quota_asset: float) -> Tuple[float,float]:
    '''
    return (daily_qty, quota_multiplier)
    '''
    quota_mul = get_quota_fixed_multiplier(asset)
    avg_price_last_n_days = th.get_avg_price_n_days(asset, ds['quota_multiplier_average_days'])
    current_price = th.get_market_price(asset)
    quota_mul *= avg_price_last_n_days / current_price
    quota_mul = min(quota_mul, ds['quota_multiplier_max'])
    daily_qty = round(quota_asset * quota_mul)
    return (daily_qty,quota_mul)


def accumulate_one(qty: float, asset: str, dry: bool):
    msg_buying(asset)

    db = Db()
    th = TradeHelper([asset])

    daily_qty,quota_mul = (qty,1) if qty else calc_daily_qty(asset, th, ds['quota_usd'])

    trader: Trader = create_trader(asset)
    if trader:
        if dry:
            actual_price = th.get_market_price(asset)
            coin_qty = daily_qty / actual_price
        else:
            actual_price, coin_qty = trader.buy_market(daily_qty)
            db.add(asset, coin_qty, actual_price)
        df = DataFrame.from_dict([{
            'asset': asset,
            'price': actual_price,
            'quota_mul': round(quota_mul,2),
            'value': coin_qty*actual_price,
            'coins/shares': coin_qty,
        }])
        print(df.to_string(index=False))
        print_account_balances()


def passes_acc_filter(asset: str, th: TradeHelper) -> Tuple[bool, str]:
    if asset not in ds['no_filter_list']:
        if ds['check_market_open']:
            if not (th.is_tradeable(asset)):
                return False, "market is closed"
        if ds['check_overprice']:
            d = th.get_distance_to_avg_percent(asset, ds['check_overprice_avg_days'])
            #print(f"{asset} distance to {ds['check_overprice_avg_days']}-day SMA : {d:.1f}%")
            if d > 1.:
                return False, "maybe overpriced"
    return True, ""


def accumulate_pre_pass(assets: List[str]) -> Tuple[float, List[str]]:
    th = TradeHelper(assets)
    total_value = 0
    i = 1
    enabled = []
    for asset in assets:
        print(f"\r{i} of {len(assets)}  ", end='', flush=True)
        i += 1

        filter_result, filter_reason = passes_acc_filter(asset, th)
        if not filter_result:
            cprint(f"{asset} filtered: {filter_reason}", "yellow")
            continue

        daily_qty,_ = calc_daily_qty(asset, th, ds['quota_usd'])
        price = th.get_market_price(asset)
        coin_qty = daily_qty / price
        value = coin_qty * price
        total_value += value
        enabled.append(asset)
    print()
    return total_value,enabled


def accumulate_main_pass(assets: List[str], dry: bool, quota_asset: float):
    db = Db()
    th = TradeHelper(assets)
    a = list()
    
    for asset in assets:
        msg_buying(asset)
        try:
            daily_qty,quota_mul = calc_daily_qty(asset, th, quota_asset)

            trader: Trader = create_trader(asset)
            if trader:
                if dry:
                    actual_price = th.get_market_price(asset)
                    coin_qty = daily_qty / actual_price
                else:
                    actual_price, coin_qty = trader.buy_market(daily_qty)
                    db.add(asset, coin_qty, actual_price)
                a.append({
                    'asset': asset,
                    'price': actual_price,
                    'quota_mul': round(quota_mul,2),
                    'value': coin_qty*actual_price,
                    'coins/shares': coin_qty,
                })
        except Exception as e:
            err(f"{asset} : was not added")
            traceback.print_exc()

    if len(a):
        df = DataFrame.from_dict(a)
        df.sort_values("value", inplace=True, ascending=False)
        print(df.to_string(index=False))
        print(f"accumulated value: ${sum(df['value']):.2f}")
    else:
        print('nothing was added.')
    print_account_balances()


def accumulate(assets: List[str], dry: bool):
    quota_asset = ds['quota_usd']
    print("calculating value of assets to be bought...")
    total_value, enabled_assets = accumulate_pre_pass(assets)
    print(f"estimated total value before limiting: {total_value}")
    if total_value > ds['total_quota_usd']:
        quota_asset *= ds['total_quota_usd'] / total_value
        quota_asset = round(quota_asset,2)
        print(f"lowering quota_usd to {quota_asset}")
    print("now buying assets...")
    accumulate_main_pass(enabled_assets, dry, quota_asset)


def remove(coin: str, qty: str, dry: bool):
    msg_selling(coin)

    db = Db()
    th = TradeHelper(db.get_syms())
    available_sell_qty = db.get_sym_available_qty(coin)
    sell_qty = 0
    m = re.match(r"([0-9]+)%", qty)
    if m:
        sell_qty = available_sell_qty * float(m[1]) / 100
    else:
        sell_qty = min(available_sell_qty, float(qty))

    trader: Trader = create_trader(coin)
    if trader:
        if dry:
            actual_price = th.get_market_price(coin)
            actual_qty = sell_qty
        else:
            actual_price, actual_qty = trader.sell_market(sell_qty)
            db.remove(coin, actual_qty, actual_price)
        df = DataFrame.from_dict([{
            'coin': coin,
            'price': actual_price,
            'coins sold': actual_qty,
            'usd sold': actual_qty*actual_price,
            'coins avail': available_sell_qty - actual_qty,
            'usd avail': (available_sell_qty - actual_qty)*actual_price,
        }])
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


def stats(hide_private_data: bool, sort_by: str):
    title("PnL")
    db = Db()
    th = TradeHelper(db.get_syms())
    assets = db.get_syms()
    asset_groups= {
        'Crypto': [x for x in assets if not is_stock(x)],
        'Stocks': [x for x in assets if is_stock(x)]
    }
    asset_group_pnl_df={}
    for asset_group in asset_groups.keys():
        title2(asset_group)
        stats_data = list()
        for coin in asset_groups[asset_group]:

            market_price = th.get_market_price(coin)
            available_qty = db.get_sym_available_qty(coin)
            pnl_data = pnl.calculate_inc_pnl(db.get_sym_trades_for_pnl(coin), market_price)

            stats_data.append({
                'asset': coin,
                'available qty': available_qty,
                'break even price': pnl_data.break_even_price,
                'current price': market_price,
                #'overpriced %': round(th.get_distance_to_avg_percent(coin, ds['check_overprice_avg_days']),1),
                'unrealized sell value': round(pnl_data.unrealized_sell_value,1),
                'r pnl': round(pnl_data.realized_pnl,1),
                'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
                'u pnl': round(pnl_data.unrealized_pnl,1),
                'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
            })
        df_pnl = DataFrame.from_dict(stats_data)
        df_pnl.sort_values(sort_by, inplace=True, ascending=False, key=lambda x: [-101 if a == "~" else a for a in x])
        columns=["asset", "break even price", "current price", "u pnl %"] if hide_private_data else None
        formatters={
            'available qty':    lambda x: f'{x:8.8f}',
        }
        print(df_pnl.to_string(index=False,formatters=formatters,columns=columns))
        print("")
        asset_group_pnl_df[asset_group] = df_pnl

    title("Portfolio Structure")
    for asset_group in asset_groups.keys():
        title2(asset_group)
        df = asset_group_pnl_df[asset_group]
        df['%'] = round(df['unrealized sell value'] / sum(df['unrealized sell value']) * 100, 1)
        df = df.sort_values('%', ascending=False)
        print(df.to_string(index=False, header=False, columns=['asset', '%']))
        print("")

    title2("By asset group")
    total_unrealized_sell_value = sum(sum(df['unrealized sell value']) for df in asset_group_pnl_df.values())
    stats_data = list()
    for asset_group in asset_groups.keys():
        stats_data.append({
            'asset_group': asset_group,
            '%' : round(sum(asset_group_pnl_df[asset_group]['unrealized sell value']) / total_unrealized_sell_value * 100, 1),
        })
    df = DataFrame.from_dict(stats_data)
    df = df.sort_values('%', ascending=False)
    print(df.to_string(index=False, header=False, columns=['asset_group', '%']))
    print("")


def technicals():
    title("Technicals")
    db = Db()
    assets = list(set( db.get_syms() + ds['auto_accumulate_list'] ))
    th = TradeHelper(assets)
    data = list()
    op_sma_len = ds['check_overprice_avg_days']
    op_header = f"distance to {op_sma_len}-day SMA %"
    print("reading data...")
    for coin in assets:
        print(".", end="", flush=True)
        data.append({
            'asset': coin,
            op_header: round(th.get_distance_to_avg_percent(coin, op_sma_len),1),
        })
    print()
    df = DataFrame.from_dict(data)
    df.sort_values(op_header, inplace=True, ascending=False)
    print(df.to_string(index=False))


def order_replay(coin: str):
    db = Db()
    orders = db.get_sym_trades_for_pnl(coin)
    for i in range(1,len(orders)+1):
        stats_data = list()
        orders_slice = orders[:i]
        last_order = orders_slice[-1]
        market_price = abs(last_order.value / last_order.qty)
        print(f"order: {last_order.side} value={last_order.value} qty={last_order.qty}")
        pnl_data = pnl.calculate_inc_pnl(orders_slice, market_price)

        stats_data.append({
            'coin': coin,
            'break_even_price': pnl_data.break_even_price,
            'current_price': market_price,
            'unrealized_sell_value': pnl_data.unrealized_sell_value,
            'r pnl': pnl_data.realized_pnl,
            'r pnl %': pnl_data.realized_pnl_percent if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
            'u pnl': pnl_data.unrealized_pnl,
            'u pnl %': pnl_data.unrealized_pnl_percent if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
        })
        
        df_pnl = DataFrame.from_dict(stats_data)
        print(df_pnl.to_string(index=False))
        print("\n")


def read_settings() -> dict:
    with open('config/dca.yml', 'r') as file:
        return yaml.safe_load(file)


def main():
    global ds
    ds = read_settings()

    parser = argparse.ArgumentParser()
    parser.add_argument('--add', action='store_const', const='True',  help='Accumulate positions')
    parser.add_argument('--remove', type=str,  help='Partially remove from a position. Arg: amount or %% of coins to remove. Requires --coin')
    parser.add_argument('--burn', type=float, help='Remove coins from equity without selling (as if lost, in other circumstances). Requires --coin')
    parser.add_argument('--close', action='store_const', const='True',  help='Close position. Requires --coin')
    parser.add_argument('--qty', type=int, help='Quota in USD for every position')
    parser.add_argument('--coin', type=str,  help='Perform an action on the specified coin only, used with --add, --remove and --close')
    parser.add_argument('--stats', action='store_const', const='True', help='Print position stats such as size, break even price, pnl and more')
    parser.add_argument('--technicals', action='store_const', const='True', help='Print technicals for coins')
    parser.add_argument('--sort-by', type=str, default='u pnl %', help='Label of the column to sort position table by')
    parser.add_argument('--order-replay', action='store_const', const='True', help='Replay orders PnL. Requires --coin')
    parser.add_argument('--balances', action='store_const', const='True', help='Print available balances on accouns')
    parser.add_argument('--hide-private-data', action='store_const', const='True', help='Do not include private data in the --stat output')
    parser.add_argument('--dry', action='store_const', const='True', help='Dry run: do not actually buy or sell, just report on what will be done')
    args = parser.parse_args()

    if args.add:
        if args.coin:
            accumulate_one(qty=args.qty, asset=args.coin, dry=args.dry)
        else:
            accumulate(assets=ds['auto_accumulate_list'], dry=args.dry)
    elif args.remove:
        if args.coin:
            remove(coin=args.coin, qty=args.remove, dry=args.dry)
        else:
            print("remove: requires --coin")
    elif args.close:
        if args.coin:
            close(coin=args.coin)
        else:
            print("close: requires --coin")
    elif args.burn:
        if args.coin:
            burn(coin=args.coin, qty=args.burn)
        else:
            print("burn: requires --coin")
    elif args.stats:
        stats(args.hide_private_data, args.sort_by)
    elif args.technicals:
        technicals()
    elif args.order_replay:
        order_replay(args.coin)
    elif args.balances:
        print_account_balances()

if __name__ == '__main__':
    main()
