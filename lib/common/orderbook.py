
from typing import List,Tuple,NamedTuple
from math import isclose



class FillPriceEstimate(NamedTuple):
    average: float # average price of the fill
    limit:   float # max fill price to be used as a limit order parameter


def estimate_fill_price(ob: List[Tuple[float,float]], qty: float) -> FillPriceEstimate:
    """ Estimate fill price by consuming order book entries as if the order have been filled at market price.
        Each order book entry is [price, qty].
    """
    #print("want qty",qty)
    if isclose(qty,0):
        return FillPriceEstimate(average=ob[0][0],limit=ob[0][0])
    fill_remaining = qty
    orders: List[Tuple[float,float]] = []
    for bucket_price,bucket_size in ob:
        #print("entry", bucket_price, bucket_size)
        this_fill = min(bucket_size, fill_remaining)
        orders.append((bucket_price, this_fill,))
        fill_remaining -= this_fill
        if isclose(fill_remaining, 0):
            break
    #print("orders",orders)
    return FillPriceEstimate(
        average= sum( [x[0]*x[1] for x in orders] ) / sum( [x[1] for x in orders] ),
        limit=max([x[0] for x in orders])
    )
