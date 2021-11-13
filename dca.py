from collections import defaultdict
import datetime, argparse, re, yaml, traceback
from pandas.core.frame import DataFrame
from math import nan
from typing import List, NamedTuple, Tuple, Dict, Any

from rich.columns import Columns
from rich.table import Table
from rich import box
from rich import print as rprint, reconfigure
reconfigure(highlight=False)

from lib.trader.trader_factory import TraderFactory
from lib.trader.trader import Trader
from lib.common.market_data import MarketData
from lib.common import accounts_balance
from lib.common import pnl
from lib.common.msg import *
from lib.common.misc import is_stock
from lib.common.widgets import track



ds = dict()

def title(name: str):
    rprint(f"\n[bold red]{name}[/]\n")

def title2(name: str):
    rprint(f"[bold white]{name}[/]")

def msg_buying(coin: str):
    rprint(f"[bold green]buying[/] : {coin}")

def msg_selling(coin: str):
    rprint(f"[bold red]selling[/] : {coin}")

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
    default_category = "other"
    if "categories" not in ds.keys():
        return default_category
    for cat,members in ds['categories'].items():
        if asset in members:
            return cat
    return default_category


class HistoricalOrder(NamedTuple):
    side:   str
    value:  float
    qty:    float
    timestamp: datetime.datetime


class TradeHelper:
    def __init__(self):
        self.market_data = MarketData()

    def get_market_price(self, coin: str) -> float:
        return 1 if coin == "USD" else self.market_data.get_market_price(coin)

    def is_tradeable(self, asset: str) -> bool:
        return self.market_data.is_tradeable(asset)

    def get_daily_change(self, coin: str) -> float:
        return self.market_data.get_daily_change(coin)

    def get_avg_price_n_days(self, coin: str, days_before: int, ma_type: str="auto") -> float:
        return self.market_data.get_avg_price_n_days(coin, days_before, ma_type)

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        return self.market_data.get_distance_to_avg_percent(coin, days_before)

    def get_fundamentals(self, asset: str) -> Dict[str, Any]:
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

    def get_syms(self) -> List:
        syms = []
        for row in self.con.execute(f"SELECT DISTINCT sym FROM dca"):
            syms.append(row[0])
        return syms

    def _get_sym_trades(self, sym: str) -> Tuple[float, float, str]:
        """returns [ [ [+-]coin_qty, price, date ] ]"""
        trades = list()
        for row in self.con.execute(f"SELECT qty,price,date FROM dca WHERE sym = '{sym}' ORDER BY date"):
            entry =(row[0], row[1], row[2] )
            trades.append(entry)
        return trades

    def get_sym_available_qty(self, sym:str) -> float:
        trades = self._get_sym_trades(sym)
        return sum([i[0] for i in trades])

    def get_sym_orders(self, sym:str) -> List[HistoricalOrder]:
        trades = self._get_sym_trades(sym)
        orders:List[HistoricalOrder] = []
        for i in trades:
            t = datetime.datetime.fromisoformat(i[2])
            if i[0] < 0:
                o = HistoricalOrder(side="SELL", value=-i[0]*i[1], qty=-i[0], timestamp=t)
            else:
                o = HistoricalOrder(side="BUY", value=i[0]*i[1], qty=i[0], timestamp=t)
            orders.append(o)
        return orders

    def get_last_buy_timestamp(self) -> datetime.datetime:
        ts = None
        for row in self.con.execute(f"SELECT date FROM dca WHERE qty > 0 ORDER BY date DESC LIMIT 1"):
            ts = datetime.datetime.fromisoformat(row[0])
        return ts


def print_account_balances():
    title("Account balances")
    df_balances = DataFrame.from_dict(accounts_balance.get_available_usd_balances_dca())
    rprint(df_balances.to_string(index=False))


def calc_daily_qty(asset: str, th: TradeHelper, quota_asset: float) -> Tuple[float,float]:
    """ return (daily_qty, quota_factor) """
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
    th = TradeHelper()

    daily_quota,quota_factor = (quota,1) if quota else calc_daily_qty(asset, th, ds['quota_usd'])

    trader: Trader = create_trader(asset)
    if trader:
        if dry:
            price = th.get_market_price(asset)
            qty = daily_quota / price
        else:
            price, qty = trader.buy_market(daily_quota,True)
            db.add(asset, qty, price)
        df = DataFrame.from_dict([{
            'asset': asset,
            'price': price,
            'quota_factor': round(quota_factor,2),
            'value': qty * price,
            'coins/shares': qty,
        }])
        rprint(df.to_string(index=False))
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
            if rsi is None:
                warn(f"{asset}: RSI calculation error")
            elif rsi > ds['check_rsi_threshold']:
                return False, f"RSI {round(rsi,2)} too high"
    return True, ""


def accumulate_pre_pass(assets: List[str]) -> Tuple[float, Dict[str,float]]:
    th = TradeHelper()
    total_value = 0
    enabled = {}
    for asset in track(assets):
        filter_result, filter_reason = passes_acc_filter(asset, th)
        if not filter_result:
            rprint(f"[bold]{asset}[/] filtered: {filter_reason}")
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
    th = TradeHelper()
    a = list()
    
    for asset,quota_factor in track(assets_quota_factors.items()):
        msg_buying(asset)
        try:
            daily_qty = quota_asset * quota_factor
            trader: Trader = create_trader(asset)
            if trader:
                if dry:
                    actual_price = th.get_market_price(asset)
                    coin_qty = daily_qty / actual_price
                else:
                    actual_price, coin_qty = trader.buy_market(daily_qty,True)
                    db.add(asset, coin_qty, actual_price)
                a.append({
                    'asset': asset,
                    'price': actual_price,
                    'quota_factor': round(quota_factor,2),
                    'value': round(coin_qty*actual_price,2),
                    'qty': coin_qty,
                })
        except Exception as e:
            err(f"{asset} : was not added")
            traceback.print_exc()

    if len(a):
        df = DataFrame.from_dict(a)
        df.sort_values("value", inplace=True, ascending=False)
        rprint(df.to_string(index=False))
        rprint(f"accumulated value: {sum(df['value']):.2f} USD")
    else:
        print('nothing was added.')
    print_account_balances()


def accumulate(assets: List[str], dry: bool):
    quota_asset = ds['quota_usd']
    print("estimating value of assets to be bought...")
    total_value, assets_quota_factors = accumulate_pre_pass(assets)
    rprint(f"estimated total value before limiting: {total_value} USD")
    if total_value > ds['total_quota_usd']:
        quota_asset *= ds['total_quota_usd'] / total_value
        quota_asset = round(quota_asset,2)
        rprint(f"lowering quota to {quota_asset} USD")
    print("now buying assets...")
    accumulate_main_pass(assets_quota_factors, dry, quota_asset)


def remove(coin: str, qty: str, dry: bool):
    msg_selling(coin)

    db = Db()
    th = TradeHelper()
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
        rprint(df.to_string(index=False))
    else:
        print('not removed.')


def burn(coin: str, qty: float):
    db = Db()
    db.burn(coin, qty)
    rprint(f"burned {qty} {coin}")


def close(coin: str):
    db = Db()
    db.delete_all(coin)
    print(f"{coin} position has been closed")



def stats(hide_private_data: bool, hide_totals: bool, single_table: bool, sort_by: str):
    title("PnL")
    db = Db()
    th = TradeHelper()
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
        if not single_table:
            title2(asset_group)
        stats_data = []
        for coin in asset_groups[asset_group]:

            market_price = th.get_market_price(coin)
            available_qty = db.get_sym_available_qty(coin)
            pnl_data = pnl.calculate_inc_pnl(db.get_sym_orders(coin), market_price)

            d={
                'asset': coin,
                'available qty': available_qty,
                'break even price': pnl_data.break_even_price,
                'current price': market_price,
                #'overpriced %': round(th.get_distance_to_avg_percent(coin, ds['check_level_cutoff_avg_days']),1),
                'value': round(pnl_data.unrealized_sell_value,2),
                'r pnl': round(pnl_data.realized_pnl,2),
                'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else nan,
                'u pnl': round(pnl_data.unrealized_pnl,2),
                'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else nan,
            }
            stats_data.append(d)
            stats_data_one_table.append(d)
        df_pnl = DataFrame.from_dict(stats_data)
        df_pnl.sort_values(sort_by, inplace=True, ascending=False, key=sort_key)

        if not single_table:
            if df_pnl.size > 0:
                print_hi_negatives(df_pnl.to_string(index=False,formatters=formatters,columns=columns,na_rep="~"))
            else:
                print("No assets")
            print()
        asset_group_pnl_df[asset_group] = df_pnl
    if single_table:
        df_pnl_one_table = DataFrame.from_dict(stats_data_one_table)
        df_pnl_one_table.sort_values(sort_by, inplace=True, ascending=False, key=sort_key)
        if df_pnl_one_table.size > 0:
            print_hi_negatives(df_pnl_one_table.to_string(index=False,formatters=formatters,columns=columns,na_rep="~"))
        else:
            print("No assets")
        print()

    title("Portfolio Structure")

    # % of each asset in a category to sum of all assets in category
    for asset_group in asset_groups.keys():
        df = asset_group_pnl_df[asset_group]
        if df.size > 0:
            df['%'] = round(df['value'] / sum(df['value']) * 100, 1)
            df['USD'] = df['value']
            df['BTC'] = round(df['USD'] / th.get_market_price("bitcoin"),6)
            df.sort_values('%', ascending=False, inplace=True)


    # % of each group to all portfolio
    stats_data = []
    for asset_group in asset_groups.keys():
        if asset_group_pnl_df[asset_group].size > 0:
            stats_data.append({
                'asset_group': asset_group,
                'USD': round(sum(asset_group_pnl_df[asset_group]['value']),2),
            })
        else:
            stats_data.append({
                'asset_group': asset_group,
                'USD' : 0,
            })
    if 'unmanaged_categories' in ds.keys():
        for um_category_name,um_category_dict in ds['unmanaged_categories'].items():
            stats_data.append({
                'asset_group': um_category_name,
                'USD': round(um_category_dict['qty'] * th.get_market_price(um_category_dict['currency']),2),
            })
    df_cats = DataFrame.from_dict(stats_data)
    df_cats['%'] = round(df_cats['USD'] / sum(df_cats['USD']) * 100,1)
    df_cats['BTC'] = df_cats['USD'] / th.get_market_price("bitcoin")
    df_cats = df_cats.sort_values('%', ascending=False)


    # for every caategory print a table
    col_list = []
    for asset_group in df_cats['asset_group']:
        if asset_group in asset_group_pnl_df.keys():
            df = asset_group_pnl_df[asset_group]
            if df.size > 0:
                if hide_private_data or hide_totals:
                    df_str = df.to_string(index=False, header=False, columns=['asset', '%'])
                else:
                    df_str = df.to_string(index=False, columns=['asset', '%', 'USD', 'BTC'])
            else:
                df_str = "(none)"
            table = Table(box=box.SIMPLE_HEAD)
            table.add_column(f"[bold white]{asset_group}[/]", justify="center")
            table.add_row(df_str)
            col_list.append(table)
    rprint(Columns(col_list, equal=True, expand=False, padding=(0, 1)))

    # print categories table
    if hide_private_data or hide_totals:
        df_str = df_cats.to_string(index=False, header=False, columns=['asset_group', '%'])
    else:
        df_str = df_cats.to_string(index=False)
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column("[bold green]by asset category[/]", justify="center")
    table.add_row(df_str)
    rprint(table)
    #rprint(Panel(df_str, title="[bold underline green]by asset category[/]", expand=False, box=box.MINIMAL))
    if not (hide_private_data or hide_totals):
        rprint(f"total value across all assets: {sum(df_cats['USD']):.2f} USD ({sum(df_cats['BTC']):.6f} BTC)")
    print()


def asset_analysis():
    title("Asset Analysis")
    assets = list(set(list(ds['asset_exchg'].keys())))
    th = TradeHelper()
    asset_groups = defaultdict(list)
    for a in assets: asset_groups[get_asset_category(a)].append(a)
    for asset_group in asset_groups.keys():
        #statusbar = StatusBar(len(asset_groups[asset_group]), 50)
        data = []
        title2(asset_group)
        i = 1
        for asset in track(asset_groups[asset_group]):
            i += 1
            d ={
                'asset': asset,
                '>200d': round(th.get_distance_to_avg_percent(asset, 200),1),
            }
            if is_stock(asset):
                fundamental_data = th.get_fundamentals(asset)
                for k,v in fundamental_data.items(): d[k] = v
            data.append(d)
        df = DataFrame.from_dict(data)
        df.sort_values(">200d", inplace=True, ascending=False)
        rprint(df.to_string(index=False, na_rep="~"))
        print()


def order_replay(asset: str):
    db = Db()
    orders:HistoricalOrder = db.get_sym_orders(asset)
    stats_data = []
    for i in range(1,len(orders)+1):
        orders_slice = orders[:i]
        last_order = orders_slice[-1]
        last_order_price = abs(last_order.value / last_order.qty)
        pnl_data = pnl.calculate_inc_pnl(orders_slice, last_order_price)

        stats_data.append({
            'date': last_order.timestamp,
            'side': last_order.side,
            'price': last_order_price,
            'qty': last_order.qty,
            'value': round(last_order.value,2),
            'break_even_price': pnl_data.break_even_price,
            'unrealized_sell_value': round(pnl_data.unrealized_sell_value, 2),
            'r pnl': round(pnl_data.realized_pnl,2),
            'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else nan,
            'u pnl': round(pnl_data.unrealized_pnl,2),
            'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else nan,
        })
    df = DataFrame.from_dict(stats_data)
    rprint(df.to_string(index=False, na_rep="~"))
    print()


def print_last_dca_time():
    db = Db()
    ts = db.get_last_buy_timestamp()
    if ts is not None:
        ts_now = datetime.datetime.now()
        tdelta = (ts_now - ts)
        rprint(f"last buy order was {ts} ({tdelta.total_seconds() / 3600:.1f} hours ago)")
    else:
        print("no buy orders found")


def read_settings() -> Dict[str, Any]:
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
    parser.add_argument('--last', action='store_const', const='True', help='Print date of last DCA bulk purchase')
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
            err("remove: requires --coin")
    elif args.close:
        if args.coin:
            close(coin=args.coin)
        else:
            err("close: requires --coin")
    elif args.burn:
        if args.coin:
            burn(coin=args.coin, qty=args.burn)
        else:
            err("burn: requires --coin")
    elif args.stats:
        stats(hide_private_data=args.hide_private_data, hide_totals=not args.calc_portfolio_value, single_table=args.single_table, sort_by=args.sort_by)
    elif args.analysis:
        asset_analysis()
    elif args.order_replay:
        order_replay(args.coin)
    elif args.balances:
        print_account_balances()
    elif args.last:
        print_last_dca_time()

if __name__ == '__main__':
    main()
