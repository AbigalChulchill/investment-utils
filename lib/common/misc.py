def is_stock(asset: str):
    # stock tickers are all uppercase
    return asset.upper() == asset

def get_decimal_count(n: float) -> int:
    return len(str(n).split(".")[1])
