from lib.common.orderbook import estimate_fill_price
from math import isclose

def test_should_return_first_price_if_qty_is_0():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    assert isclose(estimate_fill_price(ob, 0), 0.01)


def test_should_return_first_price_is_qty_is_enough():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    assert isclose(estimate_fill_price(ob, 0.5), 0.01)
    assert isclose(estimate_fill_price(ob, 1), 0.01)

def test_should_return_avg_price_is_qty_is_not_enough():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    # buy 1 x 0.01 + 0.5 x 0.1 = 0.06
    assert isclose(estimate_fill_price(ob, 1.5), 0.04)

    # buy 1 x 0.01 + 1 x 0.1 = 0.11
    assert isclose(estimate_fill_price(ob, 2), 0.055)


def test_should_return_avg_partial_fill_price_is_order_book_is_too_short():
    ob = [
        [0.01, 1],
        [0.1, 1],
    ]

    assert isclose(estimate_fill_price(ob, 3), 0.055)
    assert isclose(estimate_fill_price(ob, 4), 0.055)

