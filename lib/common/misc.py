def is_stock(asset: str):
    return asset[0] == "#"

def get_decimal_count(n: float) -> int:
    return len(str(n).split(".")[1])
