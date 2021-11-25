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
    if df is not None:
        print(df.to_string())

import yfinance as yf

t = yf.Ticker("NIO")

# get stock info
pretty_json("info", t.info)

# get historical market data
pretty_df("history", t.history(period="max"))

# show actions (dividends, splits)
pretty_df("actions",t.actions)

# show dividends
pretty_obj("dividends",t.dividends)

# show splits
pretty_obj("splits",t.splits)

# show financials
pretty_df("financials",t.financials)
pretty_df("quarterly_financials",t.quarterly_financials)

# show major holders
pretty_df("major_holders",t.major_holders)

# show institutional holders
pretty_df("institutional_holders",t.institutional_holders)

# show balance sheet
pretty_df("balance_sheet",t.balance_sheet)
pretty_df("quarterly_balance_sheet",t.quarterly_balance_sheet)

# show cashflow
pretty_df("cashflow",t.cashflow)
pretty_df("quarterly_cashflow",t.quarterly_cashflow)

# show earnings
pretty_df("earnings",t.earnings)
pretty_df("quarterly_earnings",t.quarterly_earnings)

# show sustainability
pretty_df("sustainability",t.sustainability)

# show analysts recommendations
pretty_df("recommendations",t.recommendations)

# show next event (earnings, etc)
pretty_df("calendar",t.calendar)

# show ISIN code - *experimental*
# ISIN = International Securities Identification Number
pretty_json("isin",t.isin)

# show options expirations
pretty_json("options",t.options)

# get option chain for specific expiration
#opt = option_chain('YYYY-MM-DD')
# data available via: opt.calls, opt.puts
