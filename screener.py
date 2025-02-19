import argparse, yaml
from math import nan
from pandas.core.frame import DataFrame
from lib.common.market_data import MarketData
from lib.common.widgets import simple_progress_track
from lib.common.misc import is_crypto, calc_raise_percent
from lib.common.metrics import calc_discount_score, calc_heat_score
from lib.common.id_ticker_map import get_id_sym, get_id_name
from lib.portfolio.db import Db as PortfolioDb
from lib.screener.blacklist import BlacklistDb

screener_conf = yaml.safe_load(open("config/screener.yml", "r"))


def get_list_of_assets(include_stocks: bool, include_crypto: bool, include_owned: bool, extra_tickers: list[str]):
    r = []
    if include_owned:
        dca_db = PortfolioDb()
        dca_syms = dca_db.get_syms()
        dca_nonzero_syms = [x for x in dca_syms if dca_db.get_sym_available_qty(x) > 0.1]
        r += dca_nonzero_syms

    if "additional_assets" in screener_conf:
        r += screener_conf['additional_assets']

    r = list(set(r + extra_tickers))

    blacklistdb = BlacklistDb()
    r = [ x for x in r if not blacklistdb.is_blacklisted(x)]

    r = [ x for x in r if not include_crypto or is_crypto(x) ]
    r = [ x for x in r if not include_stocks or not is_crypto(x) ]
    
    return r


class FundamentalFilter:
    def __init__(self):
        self.filter_conf = screener_conf['filter']
    
    def check(self, f: dict):
        if self.filter_conf is None:
            return True

        ok = True

        if 'min_cap' in self.filter_conf:
            ok = ok and 'cap,M' in f and f['cap,M'] >= self.filter_conf['min_cap']
        
        if 'max_price_to_earnings_ratio' in self.filter_conf:
            ok = 'tr P/E' in f or 'fw P/E' in f
            if 'tr P/E' in f:
                ok = ok and f['tr P/E'] > 0 and f['tr P/E'] <= self.filter_conf['max_price_to_earnings_ratio']
            elif 'fw P/E' in f:
                ok = ok and f['fw P/E'] > 0 and f['fw P/E'] <= self.filter_conf['max_price_to_earnings_ratio']
        
        if 'max_price_to_book_ratio' in self.filter_conf:
            ok = ok and 'P/B' in f and f['P/B'] <= self.filter_conf['max_price_to_book_ratio']

        if 'max_debt_to_equity_ratio' in self.filter_conf:
            ok = ok and 'd/e' in f and f['d/e'] <= self.filter_conf['max_debt_to_equity_ratio']

        if 'min_div_yield_percent' in self.filter_conf:
            ok = ok and 'div yield,%' in f and f['div yield,%'] >= self.filter_conf['min_div_yield_percent']

        return ok


def show_overview(assets: list[str], sort_by: str, columns: list[str], csvfile: str):
    m = MarketData()
    data = []
    ff = FundamentalFilter()
    blacklistdb = BlacklistDb()

    # processing is conservatively sequential here, to prevent triggering various order rate limits
    for asset in simple_progress_track(assets):

        def should_include_column(col):
            return columns is None or col in columns

        d ={
            'ticker': get_id_sym(asset),
            'name': get_id_name(asset),

            'sector':       nan,
            'industry':     nan,
            'supply,M':     nan,
            'cap,M':        nan,
            'vol,M':        nan,
            'vol/cap,%':    nan,
            'price':        nan,
            'chg':          nan,
            'chg%':         nan,
            'w.chg':        nan,
            'w.chg%':       nan,
            'an.chg':       nan,
            'an.chg%':      nan,
            'mean':         nan,
            'bottom':       nan,
            'top':          nan,
            'down,%':       nan,
            'up mean,%':    nan,
            'heat score':   nan,
            'discount f.':  nan,
            'tr P/E':       nan,
            'fw P/E':       nan,
            'P/B':          nan,
            'd/e':          nan,
            'div rate':     nan,
            'div yield,%':  nan,
            'expense,%':    nan,
        }

        try:
            if should_include_column("price") or should_include_column("down,%") or should_include_column("up mean,%") or should_include_column("heat score") or should_include_column("discount f."):
                market_price = m.get_market_price(asset)
                d['price'] = market_price
            if should_include_column("mean") or should_include_column("up mean,%") or should_include_column("heat score"):
                ma200_price = m.get_avg_price_n_days(asset,200)
                d['mean'] = round(ma200_price,2)
                d['up mean,%'] = round(calc_raise_percent(ma200_price,market_price),1)
            if should_include_column("heat score"):
                rsi = m.get_rsi(asset)
            if should_include_column("down,%") or should_include_column("bottom") or should_include_column("top") or should_include_column("discount f.") or should_include_column("heat score"):
                lo200,hi200 = m.get_lo_hi_n_days(asset,200)
                d['bottom'] = round(lo200,2)
                d['top'] = round(hi200,2)
            if should_include_column("chg")  or should_include_column("chg%"):
                chg,chg_p = m.get_daily_change(asset)
                d['chg'] = round(chg,2)
                d['chg%'] = round(chg_p,1)
            if should_include_column("w.chg")  or should_include_column("w.chg%"):
                wchg,wchg_p = m.get_weekly_change(asset)
                d['w.chg'] = round(wchg,2)
                d['w.chg%'] = round(wchg_p,1)
            if should_include_column("an.chg")  or should_include_column("an.chg%"):
                anchg,anchg_p = m.get_annual_change(asset)
                d['an.chg'] = round(anchg,2)
                d['an.chg%'] = round(anchg_p,1)
            if should_include_column("heat score"):
                heat_score = calc_heat_score(market_price=market_price, ma200=ma200_price, hi200=hi200, rsi=rsi)
                d['heat score'] = round(heat_score,1)
            if should_include_column("discount f."):
                discount_factor = calc_discount_score(market_price=market_price, low=lo200, high=hi200)
                d['discount f.'] = round(discount_factor,1)
            if should_include_column("supply,M"):
                supply = m.get_total_supply(asset)
                d['supply,M'] = round(supply * 0.000001,1)
            if should_include_column("cap,M") or should_include_column("vol/cap,%"):
                mcap = m.get_market_cap(asset)
                d['cap,M'] = round(mcap * 0.000001,1)
            if should_include_column("vol,M") or should_include_column("vol/cap,%"):
                vol  = m.get_total_volume(asset)
                d['vol,M'] = round(vol * 0.000001,1)
            if should_include_column("vol/cap,%"):
                vol_mcap = vol / (mcap if mcap > 0 else nan)
                d['vol/cap,%'] = round(vol_mcap * 100.0 ,1)
            if should_include_column("down,%"):
                d['down,%'] = round(calc_raise_percent(hi200,market_price),1)
        except Exception as e:
            print(f"{asset} : failed to load technical data: {e}")
            blacklistdb.add_blacklist(asset)
            continue

        if not is_crypto(asset):
            fundamental_data = m.get_fundamentals(asset)
            for k,v in fundamental_data.items():
                d[k] = v
            if ff.check(d):
                data.append(d)
        else:
            data.append(d)

    df = DataFrame.from_dict(data)
    if len(df) > 0 and sort_by is not None:
        df = df.sort_values(by=sort_by, ascending=False)
    formatters = {}
    for col in df.select_dtypes("object"):
        len_max = int(df[col].str.len().max())
        formatters[col] = lambda _,len_max=len_max: f"{_:<{len_max}s}"
    if len(df) > 0:
        if csvfile:
            df.to_csv(path_or_buf=csvfile, index=False, columns=columns, na_rep="~")
        else:
            print(df.to_string(index=False, columns=columns, formatters=formatters, na_rep="~"))
    else:
        print("no data")



def precache(assets: list[str]):
    print("precaching")
    m = MarketData()
    blacklistdb = BlacklistDb()
    for asset in simple_progress_track(assets):
        try:
            get_id_sym(asset)
            get_id_name(asset)
            m.get_total_supply(asset)
            m.get_market_cap(asset)
            if not is_crypto(asset):
                m.get_fundamentals(asset)
        except Exception as e:
            print(f"{asset} download failed ({e})")
            blacklistdb.add_blacklist(asset)
            continue


def show_rsi_filter(assets: list[str]):
    m = MarketData()
    data_oversold = []
    data_overbought = []

    min_rsi = 30
    max_rsi = 70

    # processing is conservatively sequential here, to prevent triggering various order rate limits
    for asset in simple_progress_track(assets):

        rsi = m.get_rsi(asset)

        if rsi is None:
            continue

        d ={
        "ticker": get_id_sym(asset),
        "name": get_id_name(asset),
        'rsi': round(rsi,1),
        }
        if rsi < min_rsi:
            data_oversold.append(d)
        elif rsi > max_rsi:
            data_overbought.append(d)

    print()
    if len(data_overbought):
        print("overbought")
        print(DataFrame.from_dict(data_overbought).sort_values(by="ticker", ascending=False).to_string(index=False, na_rep="~"))
        print()
    if len(data_oversold):
        print("oversold")
        print(DataFrame.from_dict(data_oversold).sort_values(by="ticker", ascending=False).to_string(index=False, na_rep="~"))
        print()



def show_dir(assets: list[str]):
    m = MarketData()

    total = 0
    ups = 0
    downs = 0

    thr_p = 0.5

    # processing is conservatively sequential here, to prevent triggering various order rate limits
    for asset in simple_progress_track(assets):
        if is_crypto(asset):
            chg,chg_p = m.get_daily_change(asset)
            if chg_p > thr_p:
                ups += 1
            elif chg_p < -thr_p:
                downs += 1
            total += 1

    ups_p = ups / total
    downs_p = downs / total
    
    if ups_p > 0.9:
        direction = "strong bullish"
    elif ups_p > 0.7:
        direction = "bullish"
    elif downs_p > 0.9:
        direction = "strong bearish"
    elif downs_p > 0.7:
        direction = "bearish"
    else:
        direction = "sideways"    
    print(f"today's crypto market direction is {direction} ({ups_p*100:.0f}% up, {downs_p*100:.0f}% down)")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--overview',action='store_const', const='True', help='show overview')
    parser.add_argument('--crypto',action='store_const', const='True', help='overview: include cryptocurrencies')
    parser.add_argument('--stocks',action='store_const', const='True', help='overview: include stocks')
    parser.add_argument('--owned',action='store_const', const='True', help='overview: include existing nonzero asset positions from DCA database')
    parser.add_argument('--group', type=str, help='ticker set to select (--overview, --precache)')
    parser.add_argument('--sort-by', type=str, default=None, help='overview: sort by column name')
    parser.add_argument('--csv', type=str, default=None, help='overview: write csv file')
    parser.add_argument('--precache', action='store_const', const='True', help='populate data cache only')
    
    parser.add_argument('--rsi',action='store_const', const='True', help='list oversold/overbought')
    parser.add_argument('--dir',action='store_const', const='True', help='detect common market direction')
    
    args = parser.parse_args()

    extra_tickers = screener_conf['asset_groups'][args.group]  if args.group else []
    assets = get_list_of_assets(include_stocks=args.stocks,include_crypto=args.crypto,include_owned=args.owned,extra_tickers=extra_tickers)

    if args.overview:
        show_overview(assets=assets, sort_by=args.sort_by, columns=screener_conf['columns'], csvfile=args.csv)
    elif args.precache:
        precache(assets=assets)
    elif args.rsi:
        show_rsi_filter(assets=assets)
    elif args.dir:
        show_dir(assets=assets)


if __name__ == '__main__':
    main()
