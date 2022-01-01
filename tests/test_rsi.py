
from math import isclose
import talib, pandas as pd


test_array = pd.Series([
    254.3,
    263.1,
    232.8,
    232.9,
    238.6,
    249.7,
    256.7,
    250.7,
    244.7,
    225.6,
    202.8,
    191.6,
    184.6,
    186.9,
    203.4,
    176.7,
    166.9,
    181.1,
    179.9,
    162.3,
    169.5,
    172.9,
    174.2,
    187.3,
    193.1,
    183.3,
    181.0,
    185.9,
    206.5,
    246.9,
    270.4,
    263.7,
    267.8,
    277.5,
    252.7,
    236.3,
    262.8,
    253.8,
])




def rsi_sma(x, length: int):
    close_delta = x.diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    up_mean = up.rolling(window=length).mean()
    down_mean = down.rolling(window=length).mean()
    rs = up_mean / down_mean
    rsi = 100 - (100/(1 + rs))
    return rsi

def rsi_ema(x, length: int):
    close_delta = x.diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    up_mean = up.ewm(span=length, min_periods=length).mean()
    down_mean = down.ewm(span=length, min_periods=length).mean()
    rs = up_mean / down_mean
    rsi = 100 - (100/(1 + rs))
    return rsi

def rsi_wilder(x, length: int):
    close_delta = x.diff()
    up = close_delta.clip(lower=0)
    down = -1 * close_delta.clip(upper=0)
    up_mean = up.ewm(com=length-1, min_periods=length).mean()
    down_mean = down.ewm(com=length-1, min_periods=length).mean()
    rs = up_mean / down_mean
    rsi = 100 - (100/(1 + rs))
    return rsi


def test_rsi():


    # TV: RSI=56.52

    #assert isclose(round(rsi_sma(test_array, 14).iat[-1],2), 66.26)
    #assert isclose(round(rsi_wilder(test_array, 14).iat[-1],2), 57.59)
    assert isclose(round(talib.RSI(test_array, 14).iat[-1],2), 56.22)

    # TV: RSI=59.36

    #assert isclose(round(rsi_sma(test_array[:-1], 14).iat[-1],2), 71.24)
    #assert isclose(round(rsi_wilder(test_array[:-1], 14).iat[-1],2), 60.61)
    assert isclose(round(talib.RSI(test_array[:-1], 14).iat[-1],2), 59.02)
   
    # TV: RSI=52.90

    #assert isclose(round(rsi_sma(test_array[:-2], 14).iat[-1],2), 67.28)
    #assert isclose(round(rsi_wilder(test_array[:-2], 14).iat[-1],2), 54.00)
    assert isclose(round(talib.RSI(test_array[:-2], 14).iat[-1],2), 52.57)
