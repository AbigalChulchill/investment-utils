from lib.common.misc import get_decimal_count, get_first_decimal_place, calc_raise_percent
from math import isclose

def test_get_decimal_count():
    assert isclose(get_decimal_count(0.0), 0)
    assert isclose(get_decimal_count(0.1), 1)
    assert isclose(get_decimal_count(0.02), 2)
    assert isclose(get_decimal_count(0.12), 2)
    assert isclose(get_decimal_count(0.123), 3)

def test_get_first_decimal_place():
    assert isclose(get_first_decimal_place(1), 0)
    assert isclose(get_first_decimal_place(0.1), 1)
    assert isclose(get_first_decimal_place(0.02), 2)
    assert isclose(get_first_decimal_place(0.003), 3)
    assert isclose(get_first_decimal_place(0.01234), 2)

def test_calc_raise_percent():
    #assert isclose(calc_raise_percent(0, 1), 1) # this should trigger assertion
    assert isclose(calc_raise_percent(1, 1), 0)
    assert isclose(calc_raise_percent(1, 1.5), 50)
    assert isclose(calc_raise_percent(1, 2), 100)
    assert isclose(calc_raise_percent(2, 1.5), -25)
    assert isclose(calc_raise_percent(2, 1), -50)
    assert isclose(calc_raise_percent(2, 0), -100)