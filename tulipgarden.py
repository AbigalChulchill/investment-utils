import argparse, yaml
from pandas.core.frame import DataFrame
from termcolor import cprint
from lib.common.market_data import MarketData
from lib.common.id_ticker_map import id_to_ticker
from lib.common.widgets import StatusBar


conf = yaml.safe_load(open('config/tulipgarden.yml', 'r'))


def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])


def technicals():
    title("Technicals")
    assets = conf['assets']
    market_data = MarketData()
    data = []
    i = 1
    statusbar = StatusBar(len(assets), 50)
    for asset in assets:
        statusbar.progress(i)
        i += 1
        data.append({
            'ticker': id_to_ticker[asset],
            '>200d': round(market_data.get_distance_to_avg_percent(asset, 200),1),
        })
    statusbar.clear()
    df = DataFrame.from_dict(data)
    df.sort_values(">200d", inplace=True, ascending=False)
    print(df.to_string(index=False, na_rep="~"))
    print()


def main():
    technicals()

if __name__ == '__main__':
    main()
