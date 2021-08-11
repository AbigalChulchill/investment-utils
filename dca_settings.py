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
    "ethereum-classic",
    "ftx-token",
    "decentraland",
]

# list of coins NOT to be accumulated when using --add with no additional parameters
auto_accumulate_black_list = [
    "cardano",
    "matic-network",
    "binancecoin",
    "symbol",
    "hoge-finance",
    "polyzap",
    "lien",
    "polycat-finance",
    "shiba-inu",
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
    "ethereum-classic": "poloniex",
    "ftx-token":        "ftx",
    "decentraland":     "binance",
}


# base quota, before any reduction
quota_usd = 50

# applied to base quota to selectively limit quota
quota_multiplier = {
    "gitcoin":          0.25,
    "dogecoin":         0.25,
    "solana":           0.5,
}

# extra coins to be purchased to match the amount of main coin
liquidity_pairs = {
#    "ethereum": "polyzap",
#    "matic-network": "polycat-finance",
#    "binancecoin": "lien",
}
