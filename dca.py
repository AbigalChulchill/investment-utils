import datetime, argparse, re, yaml, time, traceback, logging, jmespath, os.path
from collections.abc import Callable, Iterable
from abc import abstractmethod
from pandas.core.frame import DataFrame
from pandas import concat
from math import nan, isclose
from typing import List, Tuple, Dict, Any

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
from lib.portfolio.visualize import visualize_portfolio_tree_structure

ds = dict()

def title(name: str):
    rprint(f"\n[bold red]{name}[/]\n")

def title2(name: str):
    rprint(f"[bold white]{name}[/]")

def msg_buying(asset: str, value: float):
    rprint(f"[bold green]buying[/] {get_asset_desc(asset)} for {value:.2f} USD")

def msg_selling(asset: str, qty: float):
    rprint(f"[bold red]selling[/] {qty} {get_asset_desc(asset)}")



def get_quota_fixed_factor(category: str, asset: str):
    param = 'quota_fixed_factor'
    if param in ds.keys():
        if asset in ds[param].keys():
            return ds[param][asset]
        if category in ds[param].keys():
            return ds[param][category]
    return 1

def get_asset_category(asset: str) -> str:
    traverser = AssetsCompositeHierarchy(managed_only=True)
    for x in traverser.flat_list():
        if x[0] == asset:
            return x[1]
    return "/all/uncategorized"


def get_asset_desc(asset: str):
    return f"{get_id_sym(asset)} ({get_id_name(asset)})"

class TraderDecorator(Trader):
    def __init__(self, asset: str, base_trader: Trader, dcadb: Db):
        self._asset = asset
        self._base_trader= base_trader
        self._dcadb = dcadb

    def buy_market(self, qty: float, qty_in_usd: bool) -> tuple[float,float]:
        fill_price, fill_qty = self._base_trader.buy_market(qty, qty_in_usd)
        if self._dcadb:
            self._dcadb.add(self._asset, fill_qty, fill_price)
        return fill_price, fill_qty

    def sell_market(self, qty_sym: float) -> tuple[float,float]:
        fill_price, fill_qty = self._base_trader.sell_market(qty_sym)
        if self._dcadb:
            self._dcadb.remove(self._asset, fill_qty, fill_price)
        return fill_price, fill_qty 
    

def create_trader(asset: str, dcadb: Db, is_dummy: bool) -> Trader:
    if asset in ds['asset_exchg']:
        exch = ds['asset_exchg'][asset]
        if is_dummy:
            return TraderDecorator(asset,TraderFactory.create_dummy(asset, is_crypto(asset) or exch == "ftx"), dcadb=None)
        else:
            return TraderDecorator(asset,TraderFactory.create_dca(asset, exch), dcadb)
    else:
        return None


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


class ManagedAssetsHierarchy:
    def __init__(self):
        self._h = ds['categories']

    def get_hierarchy(self):
        return self._h



class UnmanagedAssetsHierarchy:
    def __init__(self):
        self._d = ds['unmanaged_categories']

    def get_list(self):
        for k,v in self._d.items():
            subcategory = "/all/" + k
            for item in v:
                yield item['name'], subcategory


class CexFiatDepositHierarchy:
    def __init__(self):
        self._df_cex_balances = accounts_balance.get_available_usd_balances_dca()

    def get_list(self):
        for _,s in self._df_cex_balances.iterrows():
            yield s['cex_name'] + "_deposit", "/all/fiat"
            yield s['cex_name'] + "_borrow", "/all/fiat"



class AssetsCompositeHierarchy:
    def __init__(self, managed_only: bool):
        managed_assets = ManagedAssetsHierarchy()
        if not managed_only:
            unmanaged_assets = UnmanagedAssetsHierarchy()
            cex_fiat_deposit = CexFiatDepositHierarchy()

        self._h =  managed_assets.get_hierarchy()

        if not managed_only:
            def create_path(h: dict, path: str):
                path = category_path.replace("/all/","")
                path_chunks = path.split("/")
                d = h
                for c in path_chunks:
                    if c not in d.keys():
                        d[c] = []
                    d = d[c]
                return d


            for asset,category_path in unmanaged_assets.get_list():
                insertion_point = jmespath.search(category_path.replace("/all/","").replace("/","."), self._h)
                if insertion_point is None:
                    insertion_point = create_path(self._h, category_path)
                insertion_point.append(asset)

            for asset,category_path in cex_fiat_deposit.get_list():
                insertion_point = jmespath.search(category_path.replace("/all/","").replace("/","."), self._h)
                if insertion_point is None:
                    insertion_point = create_path(self._h, category_path)
                insertion_point.append(asset)

    def is_managed_asset(self, asset: str) -> bool:
        def inner(branch:dict):
            for k,v in branch.items():
                if type(v) is dict:
                    yield from inner(v)
                else:
                    for a in v:
                        if a == asset:
                            yield a
        return asset in inner(ManagedAssetsHierarchy().get_hierarchy())


    def flat_list(self):
        yield from self._flat_list("/all", self._h)

    def _flat_list(self,parent_category: str, branch: dict):
        for k,v in branch.items():
            subcategory = parent_category + "/" + k
            if type(v) is dict:
                yield from self._flat_list(subcategory, v)
            else:
                for asset in v:
                    yield asset,subcategory

   
    def nodes(self):
        def _nodes_process(branch: dict):
            local_nodes = []
            for k,v in branch.items():
                if type(v) is dict:
                    local_nodes.append( {'name': k, 'children': _nodes_process(v)} )
                else:
                    local_nodes.append( {'name': k, 'children': [ {'name': asset, 'children': []}  for asset in v]} )
            return local_nodes

        return {
            'name': 'all',
            'children': _nodes_process(self._h)
            }




class ValueSource:
    @abstractmethod
    def get_value(self, asset_path: str) -> float:
        """  get available USD value of asset
        """
    def _category_component(asset_path:str) -> str:
        return os.path.dirname(asset_path)
    def _asset_component(asset_path:str) -> str:
        return os.path.basename(asset_path)

class DcaDbValueSource(ValueSource):
    def __init__(self, df_pnl:DataFrame):
        self._df = df_pnl
    def get_value(self, asset_path: str) -> float:
        asset = ValueSource._asset_component(asset_path)
        locations = self._df.loc[ self._df['id'] == asset ]
        if len(locations):
            return locations [ 'value'].sum()
        return None

class UnmanagedAssetsValueSource(ValueSource):
    def __init__(self):
        self._data = ds['unmanaged_categories']
        self._th = TradeHelper()

    def get_value(self, asset_path: str) -> float:
        category_path = ValueSource._category_component(asset_path)
        asset = ValueSource._asset_component(asset_path)
        m = re.match('^/all/(.+)', category_path)
        if m:
            group = m[1]
            if group in self._data.keys():
                entries = self._data[group]
                entry = [x for x in entries if x['name'] == asset]
                if len(entry):
                    entry = entry[0]
                    return entry['qty'] * self._th.get_market_price(entry['currency'])

        return None

"""
 fiat money on CEXes
"""
class CexFiatValueSource(ValueSource):
    def __init__(self):
        df_cex_balances = accounts_balance.get_available_usd_balances_dca()
        self._map = {}
        for _,s in df_cex_balances.iterrows():
            self._map[s['cex_name']+"_deposit"] = s['available_without_borrow']
            self._map[s['cex_name']+"_borrow"] = s['borrow']


    def get_value(self, asset_path: str) -> float:
        asset = ValueSource._asset_component(asset_path)
        if asset in self._map.keys():
            return self._map[asset]
        return None

class CompositeValueSource(ValueSource):
    def __init__(self, df_pnl:DataFrame):
        self._sources = [
            DcaDbValueSource(df_pnl),
            UnmanagedAssetsValueSource(),
            CexFiatValueSource(),
        ]
    def get_value(self, asset_path: str) -> float:
        for s in self._sources:
            v = s.get_value(asset_path)
            if v is not None:
                return v
        return 0



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

    trader: Trader = create_trader(asset, db, dry)
    if trader:
        price, qty = trader.buy_market(daily_quota,True)
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
        err(f"{get_asset_desc(asset)} not tradeable ")


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
                warn(f"{get_asset_desc(asset)}: RSI calculation error")
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
    category_traverser = AssetsCompositeHierarchy(managed_only=True)

    def matching_asset_iterator() -> Iterable[tuple[str,str]]:
        for asset_or_base_category in ds['auto_accumulate']:
            # is a category
            if "/all" in asset_or_base_category:
                for asset,category in [x for x in  category_traverser.flat_list() if re.match(f"^{asset_or_base_category}.*", x[1] ) ]:
                    yield asset,category
            # is a standalone asset
            else:
                yield asset_or_base_category,get_asset_category(asset_or_base_category)

    
    for asset,category in matching_asset_iterator():
        filter_result, filter_reason = passes_acc_filter(asset, th)
        if not filter_result:
            rprint(f"[bold]{get_asset_desc(asset)}[/] {filter_reason}, skipping")
            continue
        daily_qty,quota_factor = calc_daily_qty(category, asset, th, ds['quota_usd'])
        if isclose(quota_factor,0):
            rprint(f"[bold]{get_asset_desc(asset)}[/] quota = 0, skipping")
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
            trader: Trader = create_trader(asset, db, dry)
            if trader:
                retries = 3
                while True:
                    try:
                        actual_price, coin_qty = trader.buy_market(daily_qty,True)
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
                            warn(f"{get_asset_desc(asset)} buy failed ({e}), {retries} retries remaining")
                            retries -= 1
                            time.sleep(5)
                        else:
                            err(f"{get_asset_desc(asset)} buy failed ({e})")
                            traceback.print_exc()
                            break
            else:
                info(f"{get_asset_desc(asset)} not tradeable ")
             

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

    trader: Trader = create_trader(asset, db, dry)
    if trader:
        actual_price, actual_qty = trader.sell_market(sell_qty)
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

    def create_left_align_str_formatters(df: DataFrame) -> dict:
        formatters = {}
        for col in df.select_dtypes("object"):
            len_max = int(df[col].str.len().max())
            formatters[col] = lambda _,len_max=len_max: f"{_:<{len_max}s}"
        return formatters


    title("Positions")
    db = Db()
    th = TradeHelper()
    assets = db.get_syms()
    category_traverser = AssetsCompositeHierarchy(managed_only=False)

    d_pnl = []
    pnl_sort_key = lambda x: [-101 if a == "~" else a for a in x]
    for asset in assets:

        market_price = th.get_market_price(asset)
        qty = db.get_sym_available_qty(asset)
        pnl_data = pnl.calculate_inc_pnl(db.get_sym_orders(asset), market_price)

        d={
            'id': asset,
            'ticker': get_id_sym(asset),
            'name': get_id_name(asset),
            'break even price': pnl_data.break_even_price,
            'current price': market_price,
            'qty': qty,
            'value': round(pnl_data.unrealized_sell_value,2),
            'r pnl': round(pnl_data.realized_pnl,2),
            'r pnl %': round(pnl_data.realized_pnl_percent,1) if pnl_data.realized_pnl_percent != pnl.INVALID_PERCENT else nan,
            'u pnl': round(pnl_data.unrealized_pnl,2),
            'u pnl %': round(pnl_data.unrealized_pnl_percent,1) if pnl_data.unrealized_pnl_percent != pnl.INVALID_PERCENT else nan,
        }
        d_pnl.append(d)

    df_pnl = DataFrame.from_dict(d_pnl)
    df_pnl_nonzero = df_pnl.loc[df_pnl['value'] >= 1]
    df_pnl_zero = df_pnl.loc[df_pnl['value'] < 1]
    # split by is_crypto
    df_pnl_cc     = df_pnl_nonzero.loc[ lambda df: map(is_crypto,                  df['id']) ].sort_values(sort_by, ascending=False, key=pnl_sort_key)
    df_pnl_stocks = df_pnl_nonzero.loc[ lambda df: map(lambda x: not is_crypto(x), df['id']) ].sort_values(sort_by, ascending=False, key=pnl_sort_key)

    if df_pnl_stocks.size > 0 or df_pnl_cc.size > 0 :
        columns = ["category", "ticker","name", "break even price", "current price", "u pnl %"] if hide_private_data else ["category", "ticker", "name", "break even price", "current price", "qty", "value", "r pnl", "r pnl %", "u pnl", "u pnl %" ]
        d_totals = {'value': df_pnl['value'].sum(), 'u pnl': df_pnl['u pnl'].sum()}
        d_totals['u pnl %'] = round( calc_raise_percent( d_totals['value'] - d_totals['u pnl'], d_totals['value'] ), 2)

        dfparts = [
            DataFrame([ {"category": "crypto"} ]),
            df_pnl_cc,
            DataFrame([ {"category": "stocks"} ]),
            df_pnl_stocks,
            DataFrame([ {"category": "closed positions"} ]),
            df_pnl_zero,
        ]
        if not hide_totals:
            dfparts  +=  [
                DataFrame([ {"category": "total"} ]),
                DataFrame([ d_totals ]),
            ]
        df = concat(dfparts, ignore_index=True)
    
        formatters = create_left_align_str_formatters(df)
        formatters["qty"] = lambda _: f"{_:.8f}"
        print_hi_negatives(df.to_string(index=False,formatters=formatters,columns=columns,na_rep="~"))
    else:
        print("No assets")
    print()


    title("Portfolio Structure")

    assets_value_source = CompositeValueSource(df_pnl)

    #btcusd = th.get_market_price("bitcoin")


    ps_nodes = category_traverser.nodes()

    def _nodes_set_value(node: dict, parent_category:str):
        value = 0
        
        asset_path = parent_category + "/" + node['name']
        
        if len(node['children']):
            for ch in node['children']:
                value+= _nodes_set_value(ch, asset_path)
        else:
            value = assets_value_source.get_value(asset_path)

        node['value'] = value
        return value


    _nodes_set_value(ps_nodes,"")


    visualize_portfolio_tree_structure(ps_nodes)

    df_orphaned_assets_in_portfolio = df_pnl_nonzero.loc[ [not category_traverser.is_managed_asset(x) for x in df_pnl_nonzero['id'] ] ]
    if len(df_orphaned_assets_in_portfolio):
        warn("orphaned non-zero position assets exist :")
        print(df_orphaned_assets_in_portfolio.to_string(index=False, na_rep="~", columns=["ticker","name"]))




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
