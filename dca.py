import datetime, argparse, re, yaml, time, traceback, logging, functools
from collections import defaultdict
from collections.abc import Callable
from pandas.core.frame import DataFrame, Series
from pandas import concat
from math import nan, isclose
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
from lib.common.misc import calc_raise_percent, is_crypto
from lib.common.widgets import simple_progress_track
from lib.common.metrics import calc_discount_score
from lib.common.id_ticker_map import get_id_sym, get_id_name
from lib.portfolio.db import Db
from lib.portfolio.historical_order import HistoricalOrder

ds = dict()

def title(name: str):
    rprint(f"\n[bold red]{name}[/]\n")

def title2(name: str):
    rprint(f"[bold white]{name}[/]")

def msg_buying(coin: str, value: float):
    rprint(f"[bold green]buying[/] {coin} for {value:.2f} USD")

def msg_selling(coin: str, qty: float):
    rprint(f"[bold red]selling[/] {qty} {coin}")

def create_trader(coin: str) -> Trader:
    if coin in ds['asset_exchg']:
        return TraderFactory.create_dca(coin, ds['asset_exchg'][coin])
    else:
        return None

def create_dummy_trader(coin: str) -> Trader:
    return TraderFactory.create_dummy(coin)

def get_quota_fixed_factor(category: str, asset: str):
    param = 'quota_fixed_factor'
    if param in ds.keys():
        if asset in ds[param].keys():
            return ds[param][asset]
        if category in ds[param].keys():
            return ds[param][category]
    return 1

def get_asset_category(asset: str) -> str:
    default_category = "other"
    if "categories" not in ds.keys():
        return default_category
    for cat,members in ds['categories'].items():
        if asset in members:
            return cat
    return default_category



class TradeHelper:
    def __init__(self):
        self.market_data = MarketData()

    def get_market_price(self, coin: str) -> float:
        return 1 if coin == "USD" else self.market_data.get_market_price(coin)

    def is_tradeable(self, asset: str) -> bool:
        return self.market_data.is_tradeable(asset)

    def get_daily_change(self, coin: str) -> float:
        return self.market_data.get_daily_change(coin)[1]

    def get_avg_price_n_days(self, coin: str, days_before: int, ma_type: str="auto") -> float:
        return self.market_data.get_avg_price_n_days(coin, days_before, ma_type)

    def get_lo_hi_n_days(self, coin: str, days_before: int) -> float:
        return self.market_data.get_lo_hi_n_days(coin, days_before)

    def get_distance_to_avg_percent(self, coin: str, days_before: int) -> float:
        return self.market_data.get_distance_to_avg_percent(coin, days_before)

    def get_fundamentals(self, asset: str) -> Dict[str, Any]:
        return self.market_data.get_fundamentals(asset)

    def get_rsi(self, asset: str) -> float:
        return self.market_data.get_rsi(asset)

    def get_market_cap(self, asset: str) -> int:
        return self.market_data.get_market_cap(asset)
    
    def get_total_supply(self, asset: str) -> int:
        return self.market_data.get_total_supply(asset)

    def get_short_term_trend(self, asset: str, length_days: int) -> str:
        return self.market_data.get_short_term_trend(asset,length_days)




def print_account_balances():
    title("Account balances")
    df_balances = accounts_balance.get_available_usd_balances_dca()
    rprint(df_balances.to_string(index=False, na_rep=0))


def calc_daily_qty(category: str, asset: str, th: TradeHelper, quota_asset: float) -> Tuple[float,float]:
    """ return (daily_qty, quota_factor) """
    quota_factor = get_quota_fixed_factor(category, asset)
    daily_qty = round(quota_asset * quota_factor)
    return (daily_qty,quota_factor)


def accumulate_one(asset: str, quota: float, dry: bool):
    db = Db()
    th = TradeHelper()

    daily_quota,quota_factor = (quota,1)
    msg_buying(asset, daily_quota)

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
    else:
        err(f"{asset} not tradeable ")


def passes_acc_filter(asset: str, th: TradeHelper) -> Tuple[bool, str]:
    if asset not in ds['no_filter_list'] and get_asset_category(asset) not in ds['no_filter_categories']:
        if ds['check_market_open']:
            if not (th.is_tradeable(asset)):
                return False, "market is closed"
        if ds['check_correction']:
            trend = th.get_short_term_trend(asset, ds['check_correction_min_sequential_days'])
            if trend != 'down':
                return False, "not a correction"
        if ds['check_pump']:
            if th.get_daily_change(asset) > ds['check_pump_threshold']:
                return False, "probably pump today"
        if ds['check_rsi']:
            rsi = th.get_rsi(asset)
            if rsi is None:
                warn(f"{asset}: RSI calculation error")
            elif rsi > ds['check_rsi_threshold']:
                return False, f"RSI {round(rsi,2)} too high"
        if ds['check_discount']:
            market_price = th.get_market_price(asset)
            low,high = th.get_lo_hi_n_days(asset,200)
            discount_factor = calc_discount_score(market_price=market_price, low=low, high=high)
            if discount_factor < ds['check_discount_threshold']:
                return False, f"not enough discount ({round(discount_factor,1)}%)"       

    return True, ""


def accumulate_pre_pass() -> Tuple[float, Dict[str,float]]:
    th = TradeHelper()
    total_value = 0
    enabled = {}
    for category in ds['auto_accumulate_categories']:
        for asset in simple_progress_track(ds['categories'][category],with_item_text=False):
            filter_result, filter_reason = passes_acc_filter(asset, th)
            if not filter_result:
                rprint(f"[bold]{asset}[/] {filter_reason}, skipping")
                continue
            daily_qty,quota_factor = calc_daily_qty(category, asset, th, ds['quota_usd'])
            if isclose(quota_factor,0):
                rprint(f"[bold]{asset}[/] quota = 0, skipping")
                continue
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
    
    for asset,quota_factor in simple_progress_track(assets_quota_factors.items(),with_item_text=False):
            daily_qty = quota_asset * quota_factor
            msg_buying(asset, daily_qty)
            trader: Trader = create_trader(asset)
            if trader:
                retries = 3
                while True:
                    try:
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
                        break
                    except Exception as e:
                        if retries > 0:
                            warn(f"{asset} buy failed ({e}), {retries} retries remaining")
                            retries -= 1
                            time.sleep(5)
                        else:
                            err(f"{asset} buy failed ({e})")
                            traceback.print_exc()
                            break
            else:
                info(f"{asset} not tradeable ")
             

    if len(a):
        df = DataFrame.from_dict(a)
        df.sort_values("value", inplace=True, ascending=False)
        rprint(df.to_string(index=False))
        rprint(f"accumulated value: {sum(df['value']):.2f} USD")
    else:
        print('nothing was added.')
    print_account_balances()


def accumulate(dry: bool):
    quota_asset = ds['quota_usd']
    print("estimating value of assets to be bought...")
    total_value, assets_quota_factors = accumulate_pre_pass()
    rprint(f"estimated total value before limiting: {total_value} USD")
    if total_value > ds['total_quota_usd']:
        quota_asset *= ds['total_quota_usd'] / total_value
        quota_asset = round(quota_asset,2)
        rprint(f"lowering quota to {quota_asset} USD")
    print("now buying assets...")
    accumulate_main_pass(assets_quota_factors, dry, quota_asset)


def accumulate_btc_limit(limit: float, acc_fun: Callable):
    print(f"waiting for BTC price < {limit}")
    while True:
        th = TradeHelper()
        btc_price = th.get_market_price("bitcoin")
        print(f"BTC price = {btc_price}")
        if btc_price < limit:
            acc_fun()
            break
        time.sleep(60)


def accumulate_interval(interval_minutes: int, max_repetitions: int, acc_fun: Callable):
    print(f"accumulating every {interval_minutes} minutes")
    ts_next = 0
    iteration = 0
    while True:
        if ts_next < time.time():
            acc_fun()
            iteration += 1
            ts_next = time.time() + interval_minutes * 60

        if max_repetitions > 0 and iteration == max_repetitions:
            break

        print(f"{round((ts_next - time.time()) / 60)} minutes",end="")
        if max_repetitions >= 0:
            print(f", {max_repetitions - iteration} repetitions",end="")
        print(" remaining")
        time.sleep(60)


def remove(asset: str, qty: str, dry: bool):
    msg_selling(asset, qty)

    db = Db()
    th = TradeHelper()
    available_sell_qty = db.get_sym_available_qty(asset)
    sell_qty = 0
    m = re.match(r"([0-9]+)%", qty)
    if m:
        sell_qty = available_sell_qty * float(m[1]) / 100
    else:
        sell_qty = min(available_sell_qty, float(qty))

    trader: Trader = create_trader(asset)
    if trader:
        if dry:
            actual_price = th.get_market_price(asset)
            actual_qty = sell_qty
        else:
            actual_price, actual_qty = trader.sell_market(sell_qty)
            db.remove(asset, actual_qty, actual_price)
        df = DataFrame.from_dict([{
            'price': actual_price,
            'qty': actual_qty,
            'value': actual_qty*actual_price,
            'remaining_qty': available_sell_qty - actual_qty,
            'remaining_value': (available_sell_qty - actual_qty)*actual_price,
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


def add_ext_order(asset: str, qty: float, price: float, timestamp: str):
    db = Db()
    if qty > 0:
        db.add(asset, qty, price, timestamp)
    else:
        db.remove(asset, -qty, price, timestamp)
    print("ext order has been accounted.")


def list_positions(hide_private_data: bool, hide_totals: bool, sort_by: str):
    title("Positions")
    db = Db()
    th = TradeHelper()
    assets = db.get_syms()
    asset_groups = defaultdict(list)
    for a in assets:
        asset_groups[get_asset_category(a)].append(a)

    asset_group_pnl_df={}
    pnl_sort_key = lambda x: [-101 if a == "~" else a for a in x]
    for asset_group in asset_groups.keys():
        stats_data = []
        for coin in asset_groups[asset_group]:

            market_price = th.get_market_price(coin)
            qty = db.get_sym_available_qty(coin)
            pnl_data = pnl.calculate_inc_pnl(db.get_sym_orders(coin), market_price)

            d={
                'id': coin,
                'ticker': get_id_sym(coin),
                'name': get_id_name(coin),
                'break even price': pnl_data.break_even_price,
                'current price': market_price,
                'qty': qty,
                'value': round(pnl_data.unrealized_sell_value,2),
                'r pnl': round(pnl_data.realized_pnl,2),
                'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else nan,
                'u pnl': round(pnl_data.unrealized_pnl,2),
                'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else nan,
            }
            stats_data.append(d)
        df_pnl = DataFrame.from_dict(stats_data)
        df_pnl.sort_values(sort_by, inplace=True, ascending=False, key=pnl_sort_key)
        asset_group_pnl_df[asset_group] = df_pnl

    df_pnl_one_table = concat(asset_group_pnl_df.values())
    df_pnl_one_table_nonzero = df_pnl_one_table.loc[df_pnl_one_table['value'] >= 1]
    df_pnl_one_table_zero = df_pnl_one_table.loc[df_pnl_one_table['value'] < 1]
    # split by is_crypto
    df_pnl_one_table_cc     = df_pnl_one_table_nonzero.loc[ lambda df: map(is_crypto,                  df['id']) ].sort_values(sort_by, ascending=False, key=pnl_sort_key)
    df_pnl_one_table_stocks = df_pnl_one_table_nonzero.loc[ lambda df: map(lambda x: not is_crypto(x), df['id']) ].sort_values(sort_by, ascending=False, key=pnl_sort_key)

    if df_pnl_one_table_stocks.size > 0 or df_pnl_one_table_cc.size > 0 :
        columns = ["category", "ticker","name", "break even price", "current price", "u pnl %"] if hide_private_data else ["category", "ticker", "name", "break even price", "current price", "qty", "value", "r pnl", "r pnl %", "u pnl", "u pnl %" ]
        d_totals = {'value': df_pnl_one_table['value'].sum(), 'u pnl': df_pnl_one_table['u pnl'].sum()}
        d_totals['u pnl %'] = round( calc_raise_percent( d_totals['value'] - d_totals['u pnl'], d_totals['value'] ), 2)

        dfparts = [
            DataFrame([ {"category": "crypto"} ]),
            df_pnl_one_table_cc,
            DataFrame([ {"category": "stocks"} ]),
            df_pnl_one_table_stocks,
            DataFrame([ {"category": "closed positions"} ]),
            df_pnl_one_table_zero,
        ]
        if not hide_totals:
            dfparts  +=  [
                DataFrame([ {"category": "total"} ]),
                DataFrame([ d_totals ]),
            ]
        df = concat(dfparts, ignore_index=True)
    
        formatters = {}
        for col in df.select_dtypes("object"):
            len_max = int(df[col].str.len().max())
            formatters[col] = lambda _,len_max=len_max: f"{_:<{len_max}s}"
        formatters["qty"] = lambda _: f"{_:.8f}"
        print_hi_negatives(df.to_string(index=False,formatters=formatters,columns=columns,na_rep="~"))
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
    # create custom asset category for fiat money on CEXes
    df_cex_balances = accounts_balance.get_available_usd_balances_dca()
    df_cex_balances_liquid = df_cex_balances.loc[ df_cex_balances['liquid'] == True ]
    df_cex_balances_illiquid = df_cex_balances.loc[ df_cex_balances['liquid'] == False ]
    stats_data.append({
        'asset_group': "fiat_liquid_cex",
        'USD': round(
                  df_cex_balances_liquid['available_without_borrow'].sum() + df_cex_balances_liquid['borrow'].sum()#borrow has "-" sign
                ,2),
    })
    stats_data.append({
        'asset_group': "fiat_illiquid_cex",
        'USD': round(
                  df_cex_balances_illiquid['available_without_borrow'].sum() + df_cex_balances_illiquid['borrow'].sum()#borrow has "-" sign
                ,2),
    })


    df_assets = DataFrame.from_dict(stats_data)
    df_assets = df_assets.loc[df_assets['USD'] >= 0]
    df_assets['%'] = round(df_assets['USD'] / sum(df_assets['USD']) * 100,1)
    df_assets['BTC'] = df_assets['USD'] / th.get_market_price("bitcoin")
    df_assets = df_assets.sort_values('%', ascending=False)

    df_liabilities = DataFrame.from_dict(stats_data)
    df_liabilities = df_liabilities.loc[df_liabilities['USD'] < 0]
    df_liabilities['%'] = round(df_liabilities['USD'] / sum(df_assets['USD']) * 100,1) # % is calculated respective to size of assets
    df_liabilities['BTC'] = df_liabilities['USD'] / th.get_market_price("bitcoin")
    df_liabilities = df_liabilities.sort_values('%', ascending=True)

    # for every caategory print a table
    table = Table(box=box.SIMPLE_HEAD)
    col_list = []
    for asset_group in df_assets['asset_group']:
        if asset_group in asset_group_pnl_df.keys():
            df = asset_group_pnl_df[asset_group]
            if df.size > 0:
                if hide_private_data or hide_totals:
                    df_str = df.to_string(index=False, header=False, columns=['ticker', '%'])
                else:
                    df_str = df.to_string(index=False, columns=['ticker', '%', 'USD'])
            else:
                df_str = "(none)"
            table.add_column(f"[bold white]{asset_group}[/]", justify="center")
            col_list.append(df_str)
    table.add_row(*col_list)
    rprint(table)

    # print assets and liabilities tables
    if hide_private_data or hide_totals:
        df_assets_str = df_assets.to_string(index=False, header=False, columns=['asset_group', '%'])
        df_liabilities_str = df_liabilities.to_string(index=False, header=False, columns=['asset_group', '%'])
    else:
        df_assets_str = df_assets.to_string(index=False)
        df_liabilities_str = df_liabilities.to_string(index=False)
    table = Table(box=box.SIMPLE_HEAD)
    table.add_column(f"[bold green]assets[/]", justify="center")
    table.add_column(f"[bold yellow]liabilities[/]", justify="center")
    table.add_row(df_assets_str,df_liabilities_str)
    rprint(table)
    rprint("  **  % liabilities is calculated respective to size of assets")
    rprint()


    if not (hide_private_data or hide_totals):
        rprint(f"total value across all assets: {sum(df_assets['USD']):.2f} USD ({sum(df_assets['BTC']):.6f} BTC)")
        rprint()


def _coalesce_bucket(orders: List[HistoricalOrder]):
    return HistoricalOrder(
        side=orders[0].side,
        value=sum([x.value for x in orders]),
        qty=sum([x.qty for x in orders]),
        timestamp=orders[-1].timestamp
        )

def _coalesce_orders(orders: List[HistoricalOrder]):
    if len(orders) < 2:
        return orders

    buckets: List[List[HistoricalOrder]] = []

    bucket:List[HistoricalOrder] = []
    side = None
    for o in orders:
        if side is None: #first item
            side = o.side
            bucket.append(o)
        elif side == o.side :
            bucket.append(o)
        elif side != o.side:
            buckets.append(bucket)
            bucket = [o]
        side = o.side
    buckets.append(bucket)
    coalesced_orders = [_coalesce_bucket(x) for x in buckets]
    return coalesced_orders


def order_replay(asset: str, coalesce: bool):
    db = Db()
    orders = db.get_sym_orders(asset)
    if coalesce:
        orders = _coalesce_orders(orders)
    stats_data = []
    for i in range(1,len(orders)+1):
        orders_slice = orders[:i]
        last_order = orders_slice[-1]
        last_order_price = abs(last_order.value / last_order.qty)
        pnl_data = pnl.calculate_inc_pnl(orders_slice, last_order_price)

        stats_data.append({
            'date':  last_order.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
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

    logging.basicConfig(level=ds['log_level'] if 'log_level' in ds else logging.WARNING)


    parser = argparse.ArgumentParser()
    parser.add_argument('--add', action='store_const', const='True', help='Accumulate positions. Optional arg: USD quota, valid only if --coin also specified')
    parser.add_argument('--add-btc-limit', type=float, help='Accumulate positions automatically but wait until BTC price gets lower than specified value')
    parser.add_argument('--add-interval', type=int, help='Accumulate positions continuously every ADD-INTERVAL minutes')
    parser.add_argument('--repetitions', type=int, default=-1, help='For --add-interval, stop running after triggered for REPETITIONS times')
    parser.add_argument('--remove', action='store_const', const='True', help='Partially remove from a position')
    parser.add_argument('--dry', action='store_const', const='True', help='Dry run: do not actually buy or sell, just report on what will be done')
    parser.add_argument('--burn', type=float, help='Remove coins from equity without selling (as if lost, in other circumstances). Requires --coin')
    parser.add_argument('--close', action='store_const', const='True',  help='Close position. Requires --coin')
    parser.add_argument('--external', action='store_const', const='True',  help='Write a record to db for an add/remove of external origin. Requires --coin, --qty (can be negative if remove), --price and --timestamp')
    parser.add_argument('--coin', type=str,  help='Perform an action on the specified coin only, used with --add, --remove and --close')
    parser.add_argument('--qty', type=str,  help='USD quota to add, quantity or %% of coins/shares to remove. Requires --coin. Requires --add or --remove')
    parser.add_argument('--price', type=str,  help='Order price, used by --external')
    parser.add_argument('--timestamp', type=str,  help='Order timestamp, used by --external')
    parser.add_argument('--list-positions', action='store_const', const='True', help='Print position stats such as size, break even price, pnl and more')
    parser.add_argument('--sort-by', type=str, default='u pnl %', help='Label of the column to sort position table by')
    parser.add_argument('--hide-private-data', action='store_const', const='True', help='Do not include private data in the --stats output')
    parser.add_argument('--show-totals', action='store_const', const='True', help='Calculate total equity in --stats output')
    parser.add_argument('--order-replay', action='store_const', const='True', help='Replay orders PnL. Requires --coin')
    parser.add_argument('--coalesce', action='store_const', const='True', help='For --order-replay, merge sequential orders of same side')
    parser.add_argument('--balances', action='store_const', const='True', help='Print USD or USDT balance on each exchange account')
    parser.add_argument('--last', action='store_const', const='True', help='Print date of last DCA bulk purchase')
    args = parser.parse_args()

    if args.add:
        if args.coin:
            accumulate_one(asset=args.coin, quota=float(args.qty), dry=args.dry)
        else:
            accumulate(dry=args.dry)
    elif args.add_btc_limit:
        accumulate_btc_limit(args.add_btc_limit, lambda : accumulate(dry=args.dry) )
    elif args.add_interval:
        accumulate_interval(args.add_interval, args.repetitions, lambda : accumulate(dry=args.dry) )
    elif args.remove:
        assert args.coin
        assert args.qty
        remove(asset=args.coin, qty=args.qty, dry=args.dry)
    elif args.close:
        assert args.coin
        close(coin=args.coin)
    elif args.burn:
        assert args.coin
        burn(coin=args.coin, qty=args.burn)
    elif args.external:
        assert args.coin
        assert args.qty
        assert args.price
        assert args.timestamp
        add_ext_order(asset=args.coin, qty=float(args.qty), price=float(args.price), timestamp=datetime.datetime.fromisoformat(args.timestamp))
    elif args.list_positions:
        list_positions(hide_private_data=args.hide_private_data, hide_totals=not args.show_totals, sort_by=args.sort_by)
    elif args.order_replay:
        order_replay(args.coin, args.coalesce)
    elif args.balances:
        print_account_balances()
    elif args.last:
        print_last_dca_time()

if __name__ == '__main__':
    main()
