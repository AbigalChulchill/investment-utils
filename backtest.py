import os, math, json, requests, datetime, talib
from numpy import NaN, float64
import pandas as pd
import mplfinance as mpf



def load_candles_live(pair: str, ts_start: int, ts_end: int):
    api = "https://cryptocandledata.com"
    endpoint = "/api/candles"
    params={
        "exchange": "binance",
        "tradingPair": pair,
        "interval": "1d",
        "startDateTime": ts_start,
        "endDateTime": ts_end
        }
    resp = requests.get(api + endpoint, params=params)
    return resp.json()['candles']

def load_candles_json_live() -> str:
    days_before = 180
    ts_end = round(datetime.datetime.now().timestamp())
    ts_start = ts_end - 3600*24*days_before
    candles = []
    ts = ts_start
    while ts < ts_end:
        step = 3600*24*100
        candles = candles + load_candles_live("SOLUSDT", ts, min(ts_end,  ts + step))
        ts = ts + step
    return candles


def load_candles_json() -> str:
    cache_file:str = "cache_candles.json"
    if os.path.exists(cache_file):
        data = json.load(open(cache_file))
        print("loading cached candle data")
    else:
        data = load_candles_json_live()
        with open(cache_file, "w") as f:
            json.dump(data, f)
    return data

def load_candles() -> pd.DataFrame:
    df = pd.DataFrame.from_dict(load_candles_json())
    df['timestamp'] = pd.DatetimeIndex(pd.to_datetime(df['timestamp'], unit="ms"))
    df.set_index('timestamp', inplace=True)
    df['rsi'] = talib.RSI(df['close'], 10)
    df['ma'] = talib.MA(df['close'], 7)
    df['ma_long'] = talib.MA(df['close'], 50)
    return df


class Backend:

    def __init__(self, equity: float):
        self.usd = equity
        self.tokens = 0
        self.flag = 0 # read by StrategySimulator

    def set_market_price(self, price: float):
        self.market_price = price

    def buy(self, qty_usd: float):
        qty_usd = max(0, qty_usd)
        qty_usd = min(self.usd, qty_usd)
        #print(f"buy for ${qty_usd:.0f}")
        self.usd = self.usd - qty_usd
        self.tokens = self.tokens + (qty_usd / self.market_price)

        self.flag = 1

    def sell(self, qty_tokens: float):
        qty_tokens = max(0, qty_tokens)
        qty_tokens = min(self.tokens, qty_tokens)
        #print(f"sell {qty_tokens:.3f} tokens")
        self.tokens = self.tokens - qty_tokens
        self.usd = self.usd + (qty_tokens * self.market_price)

        self.flag = -1




def map_value_range(vab, a, b):
    #
    # map value in range [a, b] to [0, 1]
    #
    return (vab - a) / (b - a)

def remap_range(vab, a, b, x, y):
    #
    # map value vab in range [a, b] to value in range [x, y]
    #
    return x + map_value_range(vab, a, b) * (y - x)

# def map_rsi_range(rsi):
#     if rsi < 30:
#         return remap_range(rsi, 0, 30, 0.00001, 0.001) # 0...30   -> 0.001%...0.1%
#     elif rsi < 50:
#         return remap_range(rsi, 30, 50, 0.001, 0.01) # 30...50  -> 0.1%...1%
#     elif rsi < 70:
#         return remap_range(rsi, 50, 70, 0.01, 0.1) # 50...70  -> 1%...10%
#     else:
#         return remap_range(rsi, 70, 100, 0.1, 0.3) # 70...100 -> 10%...30%
def map_rsi_range(rsi):
    if rsi < 30:
        return remap_range(rsi, 0, 30, 0.002, 0.01)
    elif rsi < 70:
        return remap_range(rsi, 30, 70, 0.01, 0.1)
    else:
        return remap_range(rsi, 70, 100, 0.1, 0.5)


def test_map_rsi_range():
    for i in range(0,105, 5):
        print(f"{i} -> {map_rsi_range(i):.5f}")

#test_map_rsi_range()
#quit()


class Strategy:
    def step(self, pos: int, usd: float, tokens: float, backend: Backend):
        raise NotImplementedError()


class DcaStrategy(Strategy):
    def step(self, df: pd.DataFrame, pos: int, usd: float, tokens: float, backend: Backend):
        backend.buy(usd * 0.01)


class MaDxStrategy(Strategy):
    def step(self, df: pd.DataFrame, pos: int, usd: float, tokens: float, backend: Backend):
        ma = df['ma'][pos]
        ma1 = df['ma'][pos-1]
        ma2 = df['ma'][pos-2]
        ma3 = df['ma'][pos-3]
        ma4 = df['ma'][pos-4]
        bullish_pivot = ma4 > ma3 and ma3 > ma2 and ma2 < ma1 and ma1 < ma
        bearish_pivot = ma4 < ma3 and ma3 < ma2 and ma2 > ma1 and ma1 > ma

        ma_long = df['ma_long'][pos]
        ma_long1 = df['ma_long'][pos-1]
        bearish_cross = ma1 > ma_long1 and ma < ma_long

        if bullish_pivot:
            backend.buy(0.1 * usd)
        if bearish_cross:
            backend.sell(0.9 * tokens)


class DcaPaStrategy(Strategy):
    def step(self, df: pd.DataFrame, pos: int, usd: float, tokens: float, backend: Backend):
        bearish_engulfing = df['low'][pos] < df['low'][pos-1] and df['open'][pos] > df['close'][pos]

        if bearish_engulfing:
            backend.sell(0.9 * tokens)
        else:
            backend.buy(0.01 * usd)


class PriceWeightedDcaStrategy(Strategy):
    def step(self, df: pd.DataFrame, pos: int, usd: float, tokens: float, backend: Backend):
        w = (1800 / df['close'][pos]) ** 2
        backend.buy(w * 200)





class RsiStrategy(Strategy):
    def step(self, df: pd.DataFrame, pos: int, usd: float, tokens: float, backend: Backend):
        rsi = df['rsi'][pos]
        rsi1 = df['rsi'][pos-1]
        if not math.isnan(rsi) and not math.isnan(rsi1):
            rsi_d = rsi - rsi1
            if rsi < 50 and rsi_d <= 0: #rsi decreasing -> buy
                w = map_rsi_range(100 - rsi)
                backend.buy(w * usd)
            elif rsi > 50 and rsi_d > 0: # rsi increasing -> sell
                w = map_rsi_range(rsi)
                backend.sell(w * tokens)


class StrategySimulator:
    def __init__(self, df: pd.DataFrame, strategy: Strategy, backend: Backend, start_position: int):
        self.df = df
        self.strategy = strategy
        self.backend = backend
        self.pos = start_position
        self.df['usd'] =pd.Series(dtype=float)
        self.df['tokens'] =pd.Series(dtype=float)
        self.df['tokens$'] =pd.Series(dtype=float)
        self.df['equity'] =pd.Series(dtype=float)
        self.df['buy'] =pd.Series(dtype=float)
        self.df['sell'] =pd.Series(dtype=float)

    def step(self):
        market_price = self.df['close'][self.pos]
        self.backend.set_market_price(market_price)
        self.strategy.step(self.df, self.pos, self.backend.usd, self.backend.tokens, self.backend)
        #print(f"sim : step[{self.pos}]  usd={self.backend.usd:.0f}  tokens={self.backend.tokens:.3f}  equity={self.backend.usd + self.backend.tokens*market_price:.0f}")
        self.df['usd'][self.pos] = self.backend.usd
        self.df['tokens'][self.pos] = self.backend.tokens
        self.df['tokens$'][self.pos] = self.backend.tokens*market_price
        self.df['equity'][self.pos] = self.backend.usd + self.backend.tokens*market_price

        # if self.backend.flag > 0: self.df['buy'][self.pos] = self.df['low'][self.pos]
        # if self.backend.flag < 0: self.df['sell'][self.pos] = self.df['high'][self.pos]
        # self.backend.flag = 0

        self.pos = self.pos + 1

    def ended(self) -> bool:
        return self.pos >= len(self.df)

    def show_plot(self):
        ap2 = [
            mpf.make_addplot(self.df['ma']),
            #mpf.make_addplot(self.df['buy'], type='scatter',color='g', markersize=100,marker='^'),
            #mpf.make_addplot(self.df['sell'], type='scatter',color='r', markersize=100,marker='v'),
            mpf.make_addplot(self.df['ma_long'],panel=0),
            mpf.make_addplot(self.df['rsi'],panel=1, ylabel="RSI"),
            mpf.make_addplot(self.df['usd'],color='r', panel=2, ylabel="$"),
            mpf.make_addplot(self.df['tokens'],panel=3, ylabel="tokens"),
            mpf.make_addplot(self.df['tokens$'],color='r',panel=4, ylabel="token value in $"),
            mpf.make_addplot(self.df['equity'],color='r',panel=5, ylabel="equity"),
             ]
        mpf.plot(self.df, type='candle', main_panel=0,volume_panel=0,addplot=ap2, warn_too_much_data=999999999)


def main():
    df = load_candles()
    #df = df[450:]
    simulator = StrategySimulator(df, DcaPaStrategy(), Backend(equity=1000), start_position=0)

    while not simulator.ended():
        simulator.step()

    simulator.show_plot()

if __name__ == '__main__':
    main()

