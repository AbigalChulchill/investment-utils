import pycoingecko
import talib
import pandas as pd
from typing import List
from .. trader.binance_api import Binance as BinanceAPI



class MarketData:
    def __init__(self, coin_ids: List[str] = None):
        cg = pycoingecko.CoinGeckoAPI()

        # caching price data for all available coins at once
        # so we don't call API for every single item (because of frequency limits)

        self.price_data = cg.get_price(ids=coin_ids, vs_currencies='usd', include_24hr_change="true")

    def get_market_price(self, coin: str) -> float:
        #print(f"get_market_price {coin}")
        #try:
        #    return BinanceAPI().get_current_price(coin)
        #except:
        #    cg = pycoingecko.CoinGeckoAPI()
        #    return float(cg.get_price(ids=coin, vs_currencies='usd', include_24hr_change="false")[coin]['usd'])
        return float(self.price_data[coin]['usd'])

    def get_24h_change(self, coin: str) -> float:
        #print(f"get_24h_change {coin}")
        #try:
        #    return BinanceAPI().get_24h_change_percent(coin)
        #except:
        #    cg = pycoingecko.CoinGeckoAPI()
        #    return float(cg.get_price(ids=coin, vs_currencies='usd', include_24hr_change="true")[coin]['usd_24h_change'])
        return float(self.price_data[coin]['usd_24h_change'])

    def get_avg_price_n_days(self, coin: str, days_before: int) -> float:
        #print(f"get_avg_price_n_days {coin}")
        api = BinanceAPI()
        candles = api.get_candles(coin, "1d", limit=days_before)
        df = pd.DataFrame.from_dict(candles)
        df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
        df.set_index('timestamp', inplace=True)
        df['ma'] = talib.MA(df['close'], days_before)
        r = df['ma'][-1]
        if r != r:
            raise ValueError("ma == NaN")
        return r
