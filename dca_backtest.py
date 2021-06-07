import random
import math

def weight_function(min_price: float, price: float):
    w = min_price / price
    #w = 1
    if w <= 0:
        w = 0.01
    if w > 1:
        w = 1
    return w


def make_buy_order(position_quota: float, price: float, min_price: float) -> tuple:
    qty_usd = position_quota * weight_function(min_price, price)
    qty_btc = qty_usd / price
    return (qty_usd, qty_btc, )


def main():
    num_positions = 10000
    position_quota = 100
    price_spread = (1, 4)

    total_order_usd = 0
    total_order_btc = 0
    for i in range(num_positions):
        price = random.triangular(price_spread[0], price_spread[1])
        qty_order_usd, qty_order_btc = make_buy_order(position_quota, price, price_spread[0])
        #print(f"price {price}")
        total_order_usd = total_order_usd + qty_order_usd
        total_order_btc = total_order_btc + qty_order_btc
    avg_price = total_order_usd/total_order_btc
    print(f"average price: {avg_price:.2f}")


if __name__ == '__main__':
    main()
