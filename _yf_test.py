from yahoo_fin.stock_info import *

from lib.common.misc import print_pretty_json

t = "MRNA"


print_pretty_json(get_quote_data(t))

print_pretty_json(get_quote_table(t))

print(get_stats(t).to_string())

print(get_stats_valuation(t).to_string())

print(get_company_info(t).to_string())

