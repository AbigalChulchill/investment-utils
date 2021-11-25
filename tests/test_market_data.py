from lib.common.market_data import MarketData

def test_market_data():
    d = MarketData()
    print(d.get_market_price("bitcoin"))
    print(d.get_market_price("star-atlas-dao"))
    print(d.get_market_price("V"))
    print(d.get_market_price("genopets"))
    print(d.get_market_price("amp-token"))

    print(d._get_historical_bars("bitcoin",2).to_string(show_dimensions=True))
    print(d._get_historical_bars("star-atlas-dao",2).to_string(show_dimensions=True))
    print(d._get_historical_bars("V",2).to_string(show_dimensions=True))
    print(d._get_historical_bars("genopets",2).to_string(show_dimensions=True))
    print(d._get_historical_bars("amp-token",2).to_string(show_dimensions=True))

    print(d.get_rsi("bitcoin"))

    print(d.get_daily_change("bitcoin"))

