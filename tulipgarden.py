import argparse, yaml
from pandas.core.frame import DataFrame
from termcolor import cprint
from lib.common.market_data import MarketData
from lib.common.id_ticker_map import id_to_ticker
from lib.common.widgets import StatusBar


conf = yaml.safe_load(open('config/tulipgarden.yml', 'r'))


def title(name: str):
    cprint(f"\n{name}\n", 'red', attrs=['bold'])

def title2(name: str):
    cprint(f"  {name}", 'white', attrs=['bold'])


class TradeHelper:
    def __init__(self):
        self.market_data = MarketData()

    def get_market_price(self, coin: str) -> float:
        return self.market_data.get_market_price(coin)

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

def technicals():
    title("Technicals")
    assets = conf['assets']
    th = TradeHelper()
    data = []
    i = 1
    statusbar = StatusBar(len(assets), 50)
    for asset in assets:
        statusbar.progress(i)
        i += 1
        data.append({
            'ticker': id_to_ticker[asset],
            '>200d': round(th.get_distance_to_avg_percent(asset, 200),1),
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
