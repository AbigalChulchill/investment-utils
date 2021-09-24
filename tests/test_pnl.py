from lib.common.pnl import Order, calculate_inc_pnl, INVALID_PERCENT
from math import isclose

def test_calculate_pnl_no_buys_or_sells():
    pnl = calculate_inc_pnl(
        [],
        market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT


def test_calculate_pnl_unrealized():

    # unrealized even
    pnl = calculate_inc_pnl(
        [
            Order("BUY", value=1, qty=1),
        ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 1
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0


    # even but the sum is not exactly 0  (almost all realized) due to decimal fraction representation
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=1),
        Order("SELL",value=1, qty=1-0.00000000000000144329),
    ], market_price_now=1)
    assert isclose(pnl.unrealized_sell_value, 0, abs_tol=1e-9)
    assert isclose(pnl.unrealized_pnl, 0)
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT


    # unrealized profit
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=2),
    ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 2
    assert pnl.unrealized_pnl == 1
    assert pnl.unrealized_pnl_percent == 100

    # unrealized profit
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=2),
        Order("BUY", value=2, qty=2),
    ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 4
    assert pnl.unrealized_pnl == 4 - 3
    assert pnl.unrealized_pnl_percent == (4 - 3) / 3 * 100


    # unrealized loss
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=10, qty=5),
    ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 5
    assert pnl.unrealized_pnl == -5
    assert pnl.unrealized_pnl_percent == -50

    # 100% loss
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=10, qty=5),
    ], market_price_now=0)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == INVALID_PERCENT
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == -10
    assert pnl.unrealized_pnl_percent == -100


def test_calculate_pnl_realized():

    # breaking even
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=1),
        Order("SELL",value=1, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == 0
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT


    # realized profit
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=1),
        Order("SELL",value=5, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 4
    assert pnl.realized_pnl_percent == 400
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT

    # realized loss
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=1),
        Order("SELL",value=0.5, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == -0.5
    assert pnl.realized_pnl_percent == -50
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT

    # realized 100% loss
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=1, qty=1),
        Order("SELL",value=0, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == -1
    assert pnl.realized_pnl_percent == -100
    assert pnl.unrealized_sell_value == 0
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == INVALID_PERCENT


def test_calculate_pnl_partially_realized():

    # selling at same rate of buying
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=1, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 0
    assert pnl.realized_pnl_percent == 0
    assert pnl.unrealized_sell_value == 2
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0

    # selling at higher rate of buying
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 2
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0

    # selling at lower rate of buying
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=0.5, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == -0.5
    assert pnl.realized_pnl_percent == -50
    assert pnl.unrealized_sell_value == 2
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0


    # selling at higher rate of buying but price now is smaller
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
    ], market_price_now=0.5)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 1
    assert pnl.unrealized_pnl == -1
    assert pnl.unrealized_pnl_percent == -50

    # selling at higher rate of buying but price now is bigger
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
    ], market_price_now=2)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 4
    assert pnl.unrealized_pnl == 2
    assert pnl.unrealized_pnl_percent == 100


    # complex sequence #1
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=100, qty=1),         # 1 @ 100
        Order("BUY", value=200, qty=1),         # 1 @ 100 + 1 @ 200 = 300 / 2 =>> 2 @ 150
        Order("SELL",value=500, qty=1.9),       # remain = 0.1 @ 150,  r pnl = 500 - 285 = 215
        Order("BUY", value=1, qty=1),           # 0.1 @ 150 + 1 @ 1 = (15 + 1) / )0.1+ 1) = 16 / 1.1 =>> 1.1 @  14.5454545455
        Order("BUY", value=1, qty=1),           # 1.1 @ 14.5454545455 + 1 @ 1 =  (16 + 1) / (1.1 + 1) = 17 / 2.1 =>> 2.1 @  8.09523809524
        Order("SELL",value=100, qty=1.9),       # remain = 0.2 @ 8.09523809524,  r pnl = 100 - 15.380952381 = 84.619047619
    ], market_price_now=33)
    assert isclose(pnl.realized_pnl, 215 + 84.619047619)
    assert isclose(pnl.realized_pnl_percent, (215 + 84.619047619) / (1.9*150 + 1.9 * 8.09523809524) * 100)
    assert isclose(pnl.unrealized_sell_value, 0.2 * 33)
    assert isclose(pnl.unrealized_pnl, 0.2*33 - 0.2*8.09523809524)
    assert isclose(pnl.unrealized_pnl_percent, (0.2*33 - 0.2*8.09523809524) / (0.2*8.09523809524) * 100)

    # complex sequence #2
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),  # 3 @ 1
        Order("SELL",value=2, qty=1),  # 2 @ 1
        Order("BUY", value=1, qty=1),  # 3 @ 1
        Order("BUY", value=2, qty=1),  # 3 @ 1 + 1 @ 2 : avg price: (3 + 2) / ( 3 + 1) = 1.25
    ], market_price_now=10)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 4 * 10
    assert pnl.unrealized_pnl == 4*10 - 4*1.25
    assert pnl.unrealized_pnl_percent == (4*10 - 4*1.25) / (4*1.25) * 100



def test_calculate_pnl_realized_must_remain_constant():
    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 2
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0

    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
        Order("BUY", value=1, qty=1),
    ], market_price_now=1)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
    assert pnl.unrealized_sell_value == 3
    assert pnl.unrealized_pnl == 0
    assert pnl.unrealized_pnl_percent == 0

    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
        Order("BUY", value=1, qty=1),
        Order("BUY", value=2, qty=1),
    ], market_price_now=10)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100

    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
        Order("BUY", value=1, qty=1),
        Order("BUY", value=2, qty=1),
    ], market_price_now=1000)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100

    pnl = calculate_inc_pnl(
    [
        Order("BUY", value=3, qty=3),
        Order("SELL",value=2, qty=1),
        Order("BUY", value=1, qty=1),
        Order("BUY", value=2, qty=1),
        Order("BUY", value=0.5, qty=1),
    ], market_price_now=0)
    assert pnl.realized_pnl == 1
    assert pnl.realized_pnl_percent == 100
