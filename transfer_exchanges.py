"""Move asset between exchanges"""

import argparse, time

from lib.trader.trader_factory import TraderFactory
from lib.common.market_data import MarketData
from lib.common.msg import err, warn


def transfer_asset(asset: str, qty: float, src_ex: str, dest_ex: str, max_trade_value: float, min_spread: float):
    trader_src = TraderFactory.create_dca(asset, src_ex)
    trader_dest = TraderFactory.create_dca(asset, dest_ex)

    price = MarketData().get_market_price(asset)
    lot_size = min(max_trade_value / price, qty)
    print(f"using lot size {lot_size} based on max trade value of {max_trade_value} USD")

    transferred_qty = 0.

    while transferred_qty < qty:
        print("waiting for optimal price conditions")
        while True:
            try:
                estimated_sell_price = trader_src.estimate_fill_price(lot_size, "sell")
                estimated_buy_price = trader_dest.estimate_fill_price(lot_size, "buy")
                spread = round((estimated_sell_price - estimated_buy_price )/ estimated_sell_price * 100,2)
                print(f"current spread: {spread}%, required: >{min_spread}%", end="\r", flush=True)
                if spread >= min_spread:
                    break
                time.sleep(1)
            except Exception as e:
                warn(f"price estimate failed: {e}")
                continue

        try:
            [src_price, src_qty] = trader_src.sell_market(lot_size)
            #[src_price, src_qty] = [estimated_sell_price,lot_size]
            print(f"sold at {src_ex}: price={src_price} qty={src_qty}")
        except Exception as e:
            warn(f"sell failed: {e}")
            continue

        try:
            [dest_price, dest_qty] = trader_dest.buy_market(src_qty, qty_in_usd=False)
            #[dest_price, dest_qty] = [estimated_buy_price,lot_size]
            print(f"bought at {dest_ex}: price={dest_price} qty={dest_qty}")
        except Exception as e:
            err(f"buy failed: {e}")
            raise

        transferred_qty += lot_size

        print(f"transferred {transferred_qty} / {qty} ({transferred_qty/qty * 100:.2f}%)")
        print("delay 1s")
        time.sleep(1)
        print()

# import logging
# logging.basicConfig(level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=str, help='asset id')
    parser.add_argument('--qty', type=str, help='asset qty')
    parser.add_argument('--src', type=str, help='source exchange')
    parser.add_argument('--dest', type=str, help='destination exchange')
    parser.add_argument('--max-lot-size', type=float, default=15.0, help='max equivalent USD value of tokens/shares traded at once')
    parser.add_argument('--min-spread', type=float, default=0.1, help='min threshold diff %% between sell price and buy price, can be negative if sell price is lower than buy price')
    args = parser.parse_args()

    transfer_asset(
        asset=args.asset,
        qty=float(args.qty),
        src_ex=args.src,
        dest_ex=args.dest,
        max_trade_value=args.max_lot_size,
        min_spread=args.min_spread)


if __name__ == '__main__':
    main()
