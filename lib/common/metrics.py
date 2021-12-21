from math import sqrt
from lib.common.misc import calc_raise_percent

def calc_heat_score(market_price: float, ma200: float, hi200: float, rsi: float) -> float:
    """
    Heat Score

    Provides an estimate to how much the asset is overvalued.

    Asset looks overvalued if:
     - rsi is high
     - high above 200-day moving average
     - getting close to 200-day high

    """

    if rsi is None:
        rsi = 50

    return calc_raise_percent(ma200, market_price ) * rsi / sqrt(calc_raise_percent(market_price,hi200 ) if market_price < hi200 else 0.001)


def calc_discount_score(market_price: float, low: float, high: float) -> float:
    """
    Discount score

    How much price is down in % of the distance from high to low
    """

    return (1 - (market_price - low)/ (high - low)) * 100
