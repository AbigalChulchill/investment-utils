class TickerDict (dict):
    # if id is not listed below its ticker is assumed to be equal to id
    def __missing__(self,k):
        return k

id_to_ticker = TickerDict({
    "0x":                   "ZRX",
    "aave":                 "AAVE",
    "aleph":                "ALEPH",
    "algorand":             "ALGO",
    "alien-worlds":         "TLM",
    "allbridge":            "ABR",
    "amp-token":            "AMP",
    "arweave":              "AR",
    "aurory":               "AURY",
    "avalanche-2":          "AVAX",
    "axie-infinity":        "AXS",
    "basic-attention-token": "BAT",
    "binancecoin":          "BNB",
    "bitcoin":              "BTC",
    "cardano":              "ADA",
    "cave":                 "CAVE",
    "chiliz":               "CHZ",
    "chromaway":            "CHR",
    "cope":                 "COPE",
    "cosmos":               "ATOM",
    "curve-dao-token":      "CRV",
    "decentraland":         "MANA",
    "defi-land":            "DFL",
    "dogecoin":             "DOGE",
    "dydx":                 "DYDX",
    "enjincoin":            "ENJ",
    "ethereum-classic":     "ETC",
    "ethereum":             "ETH",
    "fantom":               "FTM",
    "flow":                 "FLOW",
    "ftx-token":            "FTT",
    "gala":                 "GALA",
    "genesysgo-shadow":     "SHDW",
    "genopets":             "GENE",
    "gitcoin":              "GTC",
    "harmony":              "ONE",
    "havven":               "SNX",
    "hedera-hashgraph":     "HBAR",
    "hoge-finance":         "HOGE",
    "illuvium":             "ILV",
    "matic-network":        "MATIC",
    "media-network":        "MEDIA",
    "monkeyball":           "MBS",
    "my-neighbor-alice":    "ALICE",
    "nexo":                 "NEXO",
    "only1":                "LIKE",
    "orca":                 "ORCA",
    "pancakeswap-token":    "CAKE",
    "polkadot":             "DOT",
    "raydium":              "RAY",
    "realy-metaverse":      "REAL",
    "ripple":               "XRP",
    "samoyedcoin":          "SAMO",
    "serum":                "SRM",
    "shiba-inu":            "SHIB",
    "solana":               "SOL",
    "solfarm":              "TULIP",
    "star-atlas-dao":       "POLIS",
    "star-atlas":           "ATLAS",
    "starlaunch":           "STARS",
    "sushi":                "SUSHI",
    "tezos":                "XTZ",
    "the-sandbox":          "SAND",
    "theta-token":          "THETA",
    "uniswap":              "UNI",
    "verasity":             "VRA",
    "yield-guild-games":    "YGG",
})
