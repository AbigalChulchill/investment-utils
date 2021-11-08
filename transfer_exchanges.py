"""Move asset between exchanges"""

import argparse

from lib.trader.trader_factory import TraderFactory


def transfer_asset(asset: str, qty: float, src_ex: str, dest_ex: str):

    trader_src = TraderFactory.create_dca(asset, src_ex)
    trader_dest = TraderFactory.create_dca(asset, dest_ex)

    [src_price, src_qty] = trader_src.sell_market(qty)
    print(f"sold at {src_ex}: price={src_price} qty={src_qty}")

    [dest_price, dest_qty] = trader_dest.buy_market(src_qty, qty_in_usd=False)
    print(f"bought at {dest_ex}: price={dest_price} qty={dest_qty}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=str, help='asset id')
    parser.add_argument('--qty', type=str, help='asset qty')
    parser.add_argument('--src', type=str, help='source exchange')
    parser.add_argument('--dest', type=str, help='destination exchange')
    args = parser.parse_args()

    transfer_asset(args.asset, args.qty, args.src, args.dest)


if __name__ == '__main__':
    main()
