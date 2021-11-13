"""Manage PancakeSwap farm"""

import argparse, yaml
from lib.trader.trader_factory import TraderFactory
from pandas import DataFrame

conf = yaml.safe_load(open('config/pancakeswap.yml', 'r'))


def buy_cake():
    print("buying CAKE...")
    ex = conf['exchange']
    quota = conf['quota']
    trader = TraderFactory.create_dca('pancakeswap-token', ex)
    price, qty = trader.buy_market(quota, qty_in_usd=True)

    df = DataFrame.from_dict([{
        'price': price,
        'value': qty * price,
        'qty': qty,
    }])
    print(df.to_string(index=False))


def transfer_cake():
    print("transferring CAKE to ...")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--buy-cake',action='store_const', const='True', help='buy daily amount of CAKE')
    parser.add_argument('--transfer-cake', action='store_const', const='True', help='transfer CAKE from exchange to BSC')
    args = parser.parse_args()

    if args.buy_cake:
        buy_cake()
    elif args.transfer_cake:
        transfer_cake()

if __name__ == '__main__':
    main()
