from lib.common.orderbook import estimate_fill_price, FillPriceEstimate
from math import isclose

def test_should_return_first_price_if_qty_is_0():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    r = estimate_fill_price(ob, 0)
    assert isclose(r.average, 0.01)
    assert isclose(r.limit, 0.01)


def test_should_return_first_price_is_qty_is_enough():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    r = estimate_fill_price(ob, 0.5)
    assert isclose(r.average, 0.01)
    assert isclose(r.limit, 0.01)

    r = estimate_fill_price(ob, 1)
    assert isclose(r.average, 0.01)
    assert isclose(r.limit, 0.01)

def test_should_return_avg_price_is_qty_is_not_enough():
    ob = [
        [0.01, 1],
        [0.1, 1],
        [1, 1],
    ]

    # buy 1 x 0.01 + 0.5 x 0.1 = 0.06
    r = estimate_fill_price(ob, 1.5)
    assert isclose(r.average, 0.04)
    assert isclose(r.limit, 0.1)

    # buy 1 x 0.01 + 1 x 0.1 + 1 * 1 = 1.11
    r = estimate_fill_price(ob, 3)
    assert isclose(r.average, 0.37)
    assert isclose(r.limit, 1)


def test_should_return_avg_partial_fill_price_is_order_book_is_too_short():
    ob = [
        [0.01, 1],
        [0.1, 1],
    ]

    r = estimate_fill_price(ob, 3)
    assert isclose(r.average, 0.055)
    assert isclose(r.limit, 0.1)

    r = estimate_fill_price(ob, 4)
    assert isclose(r.average, 0.055)
    assert isclose(r.limit, 0.1)

