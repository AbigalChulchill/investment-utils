from collections import defaultdict
import datetime, argparse, re, yaml, traceback
from pandas.core.frame import DataFrame
from termcolor import cprint
from typing import List, Tuple, Dict

from lib.trader.trader_factory import TraderFactory
from lib.trader.trader import Trader
from lib.common.market_data import MarketData
from lib.common import accounts_balance
from lib.common import pnl
from lib.common.msg import err
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

def get_quota_fixed_factor(coin: str):
    param = 'quota_fixed_factor'
    if param in ds.keys():
        if coin in ds[param].keys():
            return ds[param][coin]
    return 1

def get_asset_category(asset: str) -> str:
    if is_stock(asset):
        return "Stocks"
    else:
        return "Crypto"


class TradeHelper:
    def __init__(self, ids: list):
        self.market_data = MarketData(list(set(ids + list(ds['asset_exchg'].keys()))))

    def get_market_price(self, coin: str) -> float:
        return self.market_data.get_market_price(coin)

    def is_tradeable(self, asset: str) -> bool:
        return self.market_data.is_tradeable(asset)

    def get_daily_change(self, coin: str) -> float:
        return self.market_data.get_daily_change(coin)

    def get_avg_price_n_days(self, coin: str, days_before: int, ma_type: str="auto") -> float:
        return self.market_data.get_avg_price_n_days(coin, days_before, ma_type)

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        return self.market_data.get_distance_to_avg_percent(coin, days_before)

    def get_fundamentals(self, asset: str) -> dict:
        return self.market_data.get_fundamentals(asset)

    def get_rsi(self, asset: str) -> float:
        return self.market_data.get_rsi(asset)

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
    return (daily_qty, quota_factor)
    '''
    quota_factor = get_quota_fixed_factor(asset)
    avg_price_last_n_days = th.get_avg_price_n_days(asset, ds['quota_factor_average_days'])
    current_price = th.get_market_price(asset)
    quota_factor *= avg_price_last_n_days / current_price
    quota_factor = min(quota_factor, ds['quota_factor_max'])
    daily_qty = round(quota_asset * quota_factor)
    return (daily_qty,quota_factor)


def accumulate_one(asset: str, quota: float, dry: bool):
    msg_buying(asset)

    db = Db()
    th = TradeHelper([asset])

    daily_quota,quota_factor = (quota,1) if quota else calc_daily_qty(asset, th, ds['quota_usd'])

    trader: Trader = create_trader(asset)
    if trader:
        if dry:
            price = th.get_market_price(asset)
            qty = daily_quota / price
        else:
            price, qty = trader.buy_market(daily_quota)
            db.add(asset, qty, price)
        df = DataFrame.from_dict([{
            'asset': asset,
            'price': price,
            'quota_factor': round(quota_factor,2),
            'value': qty * price,
            'coins/shares': qty,
        }])
        print(df.to_string(index=False))
        print_account_balances()


def passes_acc_filter(asset: str, th: TradeHelper) -> Tuple[bool, str]:
    if asset not in ds['no_filter_list'] and get_asset_category(asset) not in ds['no_filter_categories']:
        if ds['check_market_open']:
            if not (th.is_tradeable(asset)):
                return False, "market is closed"
        if ds['check_level_cutoff']:
            d200 = th.get_distance_to_avg_percent(asset, 200)
            d = th.get_distance_to_avg_percent(asset, ds['check_level_cutoff_avg_days'])
            #print(f"{asset} distance to {ds['check_level_cutoff_avg_days']}-day SMA : {d:.1f}%")
            if d > ds['check_level_cutoff_threshold'] and d200 > 0: # not overpriced if below 200d
                return False, "probably too high"
        if ds['check_pump']:
            if th.get_daily_change(asset) > ds['check_pump_threshold']:
                return False, "probably pump today"
        if ds['check_rsi']:
            rsi = th.get_rsi(asset)
            if rsi is not None and rsi > ds['check_rsi_threshold']:
                return False, f"RSI {round(rsi,2)} too high"
    return True, ""


def accumulate_pre_pass(assets: List[str]) -> Tuple[float, Dict[str,float]]:
    th = TradeHelper(assets)
    total_value = 0
    i = 1
    enabled = {}
    for asset in assets:
        print(f"\r{i} of {len(assets)}  ", end='', flush=True)
        i += 1

        filter_result, filter_reason = passes_acc_filter(asset, th)
        if not filter_result:
            cprint(f"{asset} filtered: {filter_reason}", "cyan")
            continue

        daily_qty,quota_factor = calc_daily_qty(asset, th, ds['quota_usd'])
        price = th.get_market_price(asset)
        coin_qty = daily_qty / price
        value = coin_qty * price
        total_value += value
        enabled[asset] = quota_factor
    print()
    return total_value,enabled


def accumulate_main_pass(assets_quota_factors: Dict[str,float], dry: bool, quota_asset: float):
    db = Db()
    th = TradeHelper(list(assets_quota_factors.keys()))
    a = list()
    
    for asset,quota_factor in assets_quota_factors.items():
        msg_buying(asset)
        try:
            daily_qty = quota_asset * quota_factor
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
                    'quota_factor': round(quota_factor,2),
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
        print(f"accumulated value: {sum(df['value']):.2f} USD")
    else:
        print('nothing was added.')
    print_account_balances()


def accumulate(assets: List[str], dry: bool):
    quota_asset = ds['quota_usd']
    print("calculating value of assets to be bought...")
    total_value, assets_quota_factors = accumulate_pre_pass(assets)
    print(f"estimated total value before limiting: {total_value}")
    if total_value > ds['total_quota_usd']:
        quota_asset *= ds['total_quota_usd'] / total_value
        quota_asset = round(quota_asset,2)
        print(f"lowering quota_usd to {quota_asset}")
    print("now buying assets...")
    accumulate_main_pass(assets_quota_factors, dry, quota_asset)


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

def stats(hide_private_data: bool, hide_totals: bool, single_table: bool, sort_by: str):
    title("PnL")
    db = Db()
    th = TradeHelper(db.get_syms())
    assets = db.get_syms()
    asset_groups = defaultdict(list)
    for a in assets: asset_groups[get_asset_category(a)].append(a)
    asset_group_pnl_df={}
    stats_data_one_table = []
    columns=["asset", "break even price", "current price", "u pnl %"] if hide_private_data else None
    formatters={
        'available qty':    lambda x: f'{x:8.8f}',
    }
    sort_key=lambda x: [-101 if a == "~" else a for a in x]
    for asset_group in asset_groups.keys():
        title2(asset_group)
        stats_data = []
        for coin in asset_groups[asset_group]:

            market_price = th.get_market_price(coin)
            available_qty = db.get_sym_available_qty(coin)
            pnl_data = pnl.calculate_inc_pnl(db.get_sym_trades_for_pnl(coin), market_price)

            d={
                'asset': coin,
                'available qty': available_qty,
                'break even price': pnl_data.break_even_price,
                'current price': market_price,
                #'overpriced %': round(th.get_distance_to_avg_percent(coin, ds['check_level_cutoff_avg_days']),1),
                'value': round(pnl_data.unrealized_sell_value,2),
                'r pnl': round(pnl_data.realized_pnl,2),
                'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
                'u pnl': round(pnl_data.unrealized_pnl,2),
                'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else pnl.INVALID_PERCENT,
            }
            stats_data.append(d)
            stats_data_one_table.append(d)
        df_pnl = DataFrame.from_dict(stats_data)
        df_pnl.sort_values(sort_by, inplace=True, ascending=False, key=sort_key)

        if not single_table:
            if df_pnl.size > 0:
                print(df_pnl.to_string(index=False,formatters=formatters,columns=columns))
            else:
                print("No assets")
            print()
        asset_group_pnl_df[asset_group] = df_pnl
    if single_table:
        df_pnl_one_table = DataFrame.from_dict(stats_data_one_table)
        df_pnl_one_table.sort_values(sort_by, inplace=True, ascending=False, key=sort_key)
        if df_pnl_one_table.size > 0:
            print(df_pnl_one_table.to_string(index=False,formatters=formatters,columns=columns))
        else:
            print("No assets")
        print()

    title("Portfolio Structure")
    for asset_group in asset_groups.keys():
        title2(asset_group)
        df = asset_group_pnl_df[asset_group]
        if df.size > 0:
            df['%'] = round(df['value'] / sum(df['value']) * 100, 1)
            df['USD'] = df['value']
            df['BTC'] = round(df['USD'] / th.get_market_price("bitcoin"),6)
            df = df.sort_values('%', ascending=False)
            if hide_private_data or hide_totals:
                print(df.to_string(index=False, header=False, columns=['asset', '%']))
            else:
                print(df.to_string(index=False, columns=['asset', '%', 'USD', 'BTC']))
        else:
            print("No assets")
        print()

    title2("By asset group")
    total_unrealized_sell_value = sum(sum(df['value']) for df in asset_group_pnl_df.values() if df.size > 0)
    stats_data = list()
    for asset_group in asset_groups.keys():
        if asset_group_pnl_df[asset_group].size > 0:
            this_group_unrealized_sell_value = sum(asset_group_pnl_df[asset_group]['value'])
            stats_data.append({
                'asset_group': asset_group,
                '%' : round(this_group_unrealized_sell_value / total_unrealized_sell_value * 100, 1),
                'USD': round(this_group_unrealized_sell_value,2),
                'BTC': round(this_group_unrealized_sell_value / th.get_market_price("bitcoin"),6),
            })
        else:
            stats_data.append({
                'asset_group': asset_group,
                '%' : 0,
                'USD' : 0,
                'BTC' : 0,
            })
    df = DataFrame.from_dict(stats_data)
    df = df.sort_values('%', ascending=False)
    if hide_private_data or hide_totals:
        print(df.to_string(index=False, header=False, columns=['asset_group', '%']))
        print()
    else:
        print(df.to_string(index=False))
        print()
        print(f"total value across all assets: {total_unrealized_sell_value:.2f} USD ({total_unrealized_sell_value / th.get_market_price('bitcoin'):.6f})")
        print()

def statusbar(pos: int, count: int, width_chars: int):
    fill = "#"
    space = "."
    fill_chars = int(pos / count * width_chars)
    print("\rloading [", end="", flush=False)
    print(fill * fill_chars, end="", flush=False)
    print(space * (width_chars - fill_chars), end="", flush=False)
    print("]", end="", flush=True)

def asset_analysis():
    title("Asset Analysis")
    assets = ds['asset_exchg'].keys()
    th = TradeHelper([])
    asset_groups = defaultdict(list)
    for a in assets: asset_groups[get_asset_category(a)].append(a)
    for asset_group in asset_groups.keys():
        data = []
        title2(asset_group)
        i = 1
        for asset in asset_groups[asset_group]:
            statusbar(i, len(asset_groups[asset_group]), 50)
            i += 1
            d ={
                'asset': asset,
                '>200d': round(th.get_distance_to_avg_percent(asset, 200),1),
            }
            if is_stock(asset):
                fundamental_data = th.get_fundamentals(asset)
                for k,v in fundamental_data.items(): d[k] = v
            data.append(d)
        print()
        df = DataFrame.from_dict(data)
        df.sort_values(">200d", inplace=True, ascending=False)
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
    parser.add_argument('--add', action='store_const', const='True', help='Accumulate positions. Optional arg: USD quota, valid only if --coin also specified')
    parser.add_argument('--remove', action='store_const', const='True', help='Partially remove from a position')
    parser.add_argument('--dry', action='store_const', const='True', help='Dry run: do not actually buy or sell, just report on what will be done')
    parser.add_argument('--burn', type=float, help='Remove coins from equity without selling (as if lost, in other circumstances). Requires --coin')
    parser.add_argument('--close', action='store_const', const='True',  help='Close position. Requires --coin')
    parser.add_argument('--coin', type=str,  help='Perform an action on the specified coin only, used with --add, --remove and --close')
    parser.add_argument('--qty', type=str,  help='USD quota to add, quantity or %% of coins/shares to remove. Requires --coin. Requires --add or --remove')
    parser.add_argument('--stats', action='store_const', const='True', help='Print position stats such as size, break even price, pnl and more')
    parser.add_argument('--sort-by', type=str, default='u pnl %', help='Label of the column to sort position table by')
    parser.add_argument('--hide-private-data', action='store_const', const='True', help='Do not include private data in the --stats output')
    parser.add_argument('--calc-portfolio-value', action='store_const', const='True', help='Include equivalent sell value of the portfolio in --stats output')
    parser.add_argument('--single-table', action='store_const', const='True', help='Combine PnL of all assets into single table in --stats. By default uses separate table for each asset group')
    parser.add_argument('--analysis', action='store_const', const='True', help='Print fundamental and technical analysis data for assets')
    parser.add_argument('--order-replay', action='store_const', const='True', help='Replay orders PnL. Requires --coin')
    parser.add_argument('--balances', action='store_const', const='True', help='Print USD or USDT balance on each exchange account')
    args = parser.parse_args()

    if args.add:
        if args.coin:
            accumulate_one(asset=args.coin, quota=float(args.qty), dry=args.dry)
        else:
            accumulate(assets=ds['auto_accumulate_list'], dry=args.dry)
    elif args.remove:
        if args.coin:
            remove(coin=args.coin, qty=args.qty, dry=args.dry)
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
        stats(hide_private_data=args.hide_private_data, hide_totals=not args.calc_portfolio_value, single_table=args.single_table, sort_by=args.sort_by)
    elif args.analysis:
        asset_analysis()
    elif args.order_replay:
        order_replay(args.coin)
    elif args.balances:
        print_account_balances()

if __name__ == '__main__':
    main()
