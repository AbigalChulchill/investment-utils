from lib.common.metrics import calc_discount_score
from math import isclose

def test_calc_discount_score():
    assert isclose(calc_discount_score(market_price=2,      low=1, high=2),   0)
    assert isclose(calc_discount_score(market_price=1.9,    low=1, high=2),  10)
    assert isclose(calc_discount_score(market_price=1,      low=1, high=2), 100)
    assert isclose(calc_discount_score(market_price=3,      low=2, high=4),  50)
