import re
from math import isclose

def is_stock(asset: str):
    # stock tickers are all uppercase
    return asset.upper() == asset

def get_decimal_count(n: float) -> int:
    """
    Get number of digits after decimal point
    n = 0.0 -> 0
    n = 0.1 -> 1
    n = 0.02 -> 2
    n = 0.12 -> 2
    n = 0.123 -> 3
    """
    if isclose(n, 0):
        return 0
    return len(str(n).split(".")[1])

def get_first_decimal_place(n: float) -> int:
    """
    Get position index of the first nonzero digit after decimal point
    n = 0.1 -> 1
    n = 0.02 -> 2
    n = 0.003 -> 3
    n = 0.01234 -> 2
    """
    fraction = str(n).split(".")[1]
    m = re.match(r"(0+)[1-9]+", fraction)
    if m:
        return len(m[1]) + 1
    else:
        return 1

def calc_raise_percent(base: float, tested: float):
    """
    Value of tested as a fraction*100 of base
    """
    assert not isclose(base, 0)
    return (tested - base) / base * 100.