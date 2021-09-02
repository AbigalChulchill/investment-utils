import json
def title(t):
    print("\n\n")
    print("-----------------------------")
    print(t)
    print("-----------------------------")

def pretty_obj(t,o):
    title(t)
    print(o)

def pretty_json(t,s):
    title(t)
    print(json.dumps(s, indent=4, sort_keys=True))

def pretty_df(t,df):
    title(t)
    print(df.to_string())

import yfinance as yf

msft = yf.Ticker("MSFT")

# get stock info
pretty_json("msft.info", msft.info)

# get historical market data
pretty_df("msft.history", msft.history(period="max"))

# show actions (dividends, splits)
pretty_df("msft.actions",msft.actions)

# show dividends
pretty_obj("msft.dividends",msft.dividends)

# show splits
pretty_obj("msft.splits",msft.splits)

# show financials
pretty_df("msft.financials",msft.financials)
pretty_df("msft.quarterly_financials",msft.quarterly_financials)

# show major holders
pretty_df("msft.major_holders",msft.major_holders)

# show institutional holders
pretty_df("msft.institutional_holders",msft.institutional_holders)

# show balance sheet
pretty_df("msft.balance_sheet",msft.balance_sheet)
pretty_df("msft.quarterly_balance_sheet",msft.quarterly_balance_sheet)

# show cashflow
pretty_df("msft.cashflow",msft.cashflow)
pretty_df("msft.quarterly_cashflow",msft.quarterly_cashflow)

# show earnings
pretty_df("msft.earnings",msft.earnings)
pretty_df("msft.quarterly_earnings",msft.quarterly_earnings)

# show sustainability
pretty_df("msft.sustainability",msft.sustainability)

# show analysts recommendations
pretty_df("msft.recommendations",msft.recommendations)

# show next event (earnings, etc)
pretty_df("msft.calendar",msft.calendar)

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
pretty_json("msft.isin",msft.isin)

# show options expirations
pretty_json("msft.options",msft.options)

# get option chain for specific expiration
#opt = msft.option_chain('YYYY-MM-DD')
# data available via: opt.calls, opt.puts
