#
# Move an asset from one exchange to another
#

import argparse, time

from lib.trader.trader_factory import TraderFactory
from lib.common.market_data import MarketData
from lib.common.msg import err, warn
from lib.common.misc import get_first_decimal_place

from rich import print as rprint


def transfer_asset(asset: str, qty: str, src_ex: str, dest_ex: str, max_trade_value: float, exact_trade_qty: float, min_spread: float):
    trader_src = TraderFactory.create_dca(asset, src_ex)
    trader_dest = TraderFactory.create_dca(asset, dest_ex)

    if qty == "all" or qty == 0:
        qty = trader_src.get_available_qty()
    else:
        qty = float(qty)

    price = MarketData().get_market_price(asset)
    if exact_trade_qty is not None:
        lot_size = exact_trade_qty
    else:
        lot_size = max_trade_value / price
        lot_size = round(lot_size, get_first_decimal_place(lot_size))
    lot_size = min(lot_size, qty)
    rprint(f"[bold blue]will transfer {qty} using lot size {lot_size} based on max trade value of {max_trade_value} USD[/]")

    transferred_qty = 0.

    while transferred_qty < qty:

        # ensure lot size is not bigger that the amount that is left to transfer
        lot_size = min(lot_size, qty - transferred_qty)

        estimated_sell_price = None
        estimated_buy_price = None
        spread_range : tuple[float,float] = (100,-100)
        waited_for_spread = 0
        while True:
            try:
                estimated_sell_price = trader_src.estimate_fill_price(lot_size, "sell")
                estimated_buy_price = trader_dest.estimate_fill_price(lot_size, "buy")
                spread = round((estimated_sell_price.average - estimated_buy_price.average )/ estimated_sell_price.average * 100,2)
                spread_range = ( min(spread_range[0], spread), max(spread_range[1], spread) )
                rprint(f"[bold blue]{asset}[/]  transferred {transferred_qty}/{qty} ({transferred_qty/qty * 100:.2f}%)  current spread: {spread}%, required: >{min_spread}%  ranges {spread_range[0]}% to {spread_range[1]}%   {waited_for_spread/60:.1f}min            ", end="\r", flush=True)
                if spread >= min_spread:
                    waited_for_spread = 0
                    break
                time.sleep(1)
                waited_for_spread += 1
            except Exception as e:
                warn(f"price estimate failed: {e}")
                continue
        print()

        try:
            [src_price, src_qty] = trader_src.sell_market(lot_size)
            rprint(f"[red]sold[/] at {src_ex}: price={src_price} qty={src_qty}")
        except Exception as e:
            warn(f"sell failed: {e}")
            continue

        try:
            [dest_price, dest_qty] = trader_dest.buy_market(src_qty, qty_in_usd=False)
            rprint(f"[green]bought[/] at {dest_ex}: price={dest_price} qty={dest_qty}")

            if (abs(src_qty - dest_qty) / src_qty) > 0.002:           # > 0.2% diff should be beyond  the commission charges, so most likely indicates something is wrong
                raise RuntimeError(f"{dest_ex} is unable to buy same qty. Please check balances!")

        except Exception as e:
            err(f"buy failed: {e}")
            raise

        transferred_qty += src_qty

        print("....")
        time.sleep(1)


# import logging
# logging.basicConfig(level=logging.DEBUG)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--asset', type=str, help='asset id')
    parser.add_argument('--qty', type=str, default="all", help='asset qty')
    parser.add_argument('--src', type=str, help='source exchange')
    parser.add_argument('--dest', type=str, help='destination exchange')
    parser.add_argument('--max-lot-size', type=float, default=15.0, help='max equivalent USD value of tokens/shares traded at once')
    parser.add_argument('--exact-lot-qty', type=float, default=None, help='exact amout of tokens/shares traded at once')
    parser.add_argument('--min-spread', type=float, default=0.1, help='min threshold diff %% between sell price and buy price, can be negative if sell price is lower than buy price')
    args = parser.parse_args()

    transfer_asset(
        asset=args.asset,
        qty=args.qty,
        src_ex=args.src,
        dest_ex=args.dest,
        max_trade_value=args.max_lot_size,
        exact_trade_qty=args.exact_lot_qty,
        min_spread=args.min_spread)


if __name__ == '__main__':
    main()
