import argparse, yaml
from typing import Dict, Any
from pandas.core.frame import DataFrame
from math import nan, sqrt
from lib.common.market_data import MarketData
from lib.common.widgets import track
from lib.common.misc import is_stock, calc_raise_percent


screener_conf = yaml.safe_load(open('config/screener.yml', 'r'))


def get_list_of_assets():
   dca_conf = yaml.safe_load(open('config/dca.yml', 'r'))
   return list( set( list(dca_conf["asset_exchg"].keys()) + screener_conf['additional_assets']) )


def calc_heat_score(market_price: float, ma200: float, hi200: float, rsi: float):
    """
    Heat Score

    Provides an estimate to how much the asset is overvalued.

    Asset looks overvalued if:
     - rsi is high
     - high above 200-day moving average
     - getting close to 200-day high

    """

    return calc_raise_percent(ma200, market_price ) * rsi / sqrt(calc_raise_percent(market_price,hi200 ) if market_price < hi200 else 0.001)



def table(sort_by: str):
    assets =get_list_of_assets()
    m = MarketData()
    data_stocks = []
    data_others = []
    for asset in track(assets):

        market_price = m.get_market_price(asset)
        ma200_price = m.get_avg_price_n_days(asset,200)
        rsi = m.get_rsi(asset)
        lo200,hi200 = m.get_lo_hi_n_days(asset,200)
        chg,chg_p = m.get_daily_change(asset)
        heat_score = calc_heat_score(market_price=market_price, ma200=ma200_price, hi200=hi200, rsi=rsi)

        d ={
        "asset": asset,
        'market cap,M': round(m.get_market_cap(asset) * 0.000001,1),
        'total supply,M': round(m.get_total_supply(asset) * 0.000001,1),
        'market price': market_price,
        'chg':  round(chg,2),
        'chg%':  round(chg_p,1),
        '200d SMA': round(ma200_price,2),
        '200d low': round(lo200,2),
        '200d high': round(hi200,2),
        # 'cp>MA200': round( calc_raise_percent(ma200_price, market_price ),1),
        #'rsi': round(rsi,2),
        'heat_score': round(heat_score,1),
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
    parser.add_argument('--sort-by', type=str, default='market cap,M', help='Label of the column to sort screener table by')
    args = parser.parse_args()

    table(sort_by=args.sort_by)


if __name__ == '__main__':
    main()
