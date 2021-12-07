
from typing import List,Tuple
from math import isclose

def estimate_fill_price(ob: List[Tuple[float,float]], qty: float) -> float:
    """ Estimate fill price by consuming order book entries as if the order have been filled at market price.
        Each order book entry is [price, qty].
    """
    if isclose(qty,0):
        return ob[0][0]
    fill_remaining = qty
    orders: List[Tuple[float,float]] = []
    for price,qty in ob:
        this_fill = min(qty, fill_remaining)
        orders.append((price, this_fill,))
        fill_remaining -= this_fill
        if isclose(fill_remaining, 0):
            break
    avg_price = sum( [x[0]*x[1] for x in orders] ) / sum( [x[1] for x in orders] )
    return avg_price
