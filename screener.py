import argparse, yaml
from math import nan
from pandas.core.frame import DataFrame
from lib.common.market_data import MarketData
from lib.common.widgets import simple_progress_track
from lib.common.misc import is_stock, calc_raise_percent
from lib.common.metrics import calc_discount_score, calc_heat_score

screener_conf = yaml.safe_load(open('config/screener.yml', 'r'))


def get_list_of_assets():
   dca_conf = yaml.safe_load(open('config/dca.yml', 'r'))

   return sorted([*{*list(dca_conf["asset_exchg"].keys()) + screener_conf['additional_assets']}])


def table(sort_by: str):
    assets =get_list_of_assets()
    m = MarketData()
    data_stocks = []
    data_others = []

    # processing is conservatively sequential here, to prevent triggering various order rate limits
    for asset in simple_progress_track(assets):

        market_price = m.get_market_price(asset)
        ma200_price = m.get_avg_price_n_days(asset,200)
        rsi = m.get_rsi(asset)
        lo200,hi200 = m.get_lo_hi_n_days(asset,200)
        chg,chg_p = m.get_daily_change(asset)
        heat_score = calc_heat_score(market_price=market_price, ma200=ma200_price, hi200=hi200, rsi=rsi)
        discount_factor = calc_discount_score(market_price=market_price, low=lo200, high=hi200)
        supply = m.get_total_supply(asset)
        mcap = m.get_market_cap(asset)
        vol  = m.get_total_volume(asset)
        vol_mcap = vol / (mcap if mcap > 0 else nan)

        d ={
        "asset": asset,
        'supply,M': round(supply * 0.000001,1),
        'cap,M': round(mcap * 0.000001,1),
        'vol,M': round(vol * 0.000001,1),
        'vol % of cap': round(vol_mcap * 100.0 ,1),
        'price': market_price,
        'chg':  round(chg,2),
        'chg%':  round(chg_p,1),
        'mean': round(ma200_price,2),
        'bottom': round(lo200,2),
        'top': round(hi200,2),
        '% from top': round(calc_raise_percent(hi200,market_price),1),
        '% up mean': round(calc_raise_percent(ma200_price,market_price),1),
        'heat_score': round(heat_score,1),
        'discount_factor': round(discount_factor,1),
        
        }
        if is_stock(asset):
            fundamental_data = m.get_fundamentals(asset)
            for k,v in fundamental_data.items():
                d[k] = v
            data_stocks.append(d)
        else:
            data_others.append(d)
    df_others = DataFrame.from_dict(data_others).sort_values(by=sort_by, ascending=False)
    df_stocks = DataFrame.from_dict(data_stocks).sort_values(by=sort_by, ascending=False)
    print(df_others.append(df_stocks).to_string(index=False, na_rep="~"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--overview',action='store_const', const='True', help='show overview')
    parser.add_argument('--sort-by', type=str, default='cap,M', help='Label of the column to sort screener table by')
    args = parser.parse_args()

    table(sort_by=args.sort_by)


if __name__ == '__main__':
    main()
