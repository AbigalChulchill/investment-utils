# list of known coin ids
coin_ids = [
    "bitcoin",
    "dogecoin",
    "binancecoin",
    "ethereum",
    "matic-network",
    "cardano",
    "ripple",
    "solana",
    "gitcoin",
    "symbol",
    "shiba-inu",
    "hoge-finance",
    "polyzap",
    "lien",
    "polycat-finance",
    "curve-dao-token",
    "aave",
    "0x",
    "havven",
]

# list of coins NOT to be accumulated when using --add with no additional parameters
auto_accumulate_black_list = [
    "cardano",
    "binancecoin",
    "symbol",
    "hoge-finance",
    "polyzap",
    "lien",
    "polycat-finance",
]

# map coin id to exchange
coin_exchg = {
    "bitcoin":          "poloniex",
    "dogecoin":         "poloniex",
    "ethereum":         "poloniex",
    "matic-network":    "poloniex",
    "cardano":          "poloniex",
    "ripple":           "poloniex",
    "gitcoin":          "binance",
    "shiba-inu":        "poloniex",
    "solana":           "ftx",
    "curve-dao-token":  "poloniex",
    "aave":             "poloniex",
    "0x":               "poloniex",
    "havven":           "poloniex",
}


# base quota used if price == base_price
quota_usd = 100

# applied to base quota to selectively limit quota
quota_multiplier = {
    "gitcoin":          0.25,
    "shiba-inu":        0.25,
    "solana":           0.5,
}

# for current quota weight function, base price is the price when quota weight is 1
base_price = {
    "bitcoin":          15000,
    "ethereum":         1200,
    "matic-network":    0.3,
    "cardano":          1.0,
    "binancecoin":      50,
    "dogecoin":         0.05,
    "solana":           20,
    "ripple":           0.24,
    "gitcoin":          4,
    "shiba-inu":        0.000001,
    "polycat-finance":  12,
    "curve-dao-token":  0.64,
    "aave":             87,
    "0x":               0.3,
    "havven":           4,
}

# quota weight is another multiplier applied to quota
def get_quota_weight(coin: str, price: float):
    # As price goes up, weight decreases.
    # When price approaches base_price weight approaches 1.
    return min(1, base_price[coin] / price)


# extra coins to be purchased to match the amount of main coin
liquidity_pairs = {
#    "ethereum": "polyzap",
#    "matic-network": "polycat-finance",
#    "binancecoin": "lien",
}
