reports_dir="reports"
[ ! -d "$reports_dir" ] && mkdir "$reports_dir"


# python bots_demo.py --strategy=DCA_ConstQuota           --strategy-args=dca_base_quota=100                              --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_ConstQuota.txt
###
# Results for above:
# 17.4 @ 8400
###


# python bots_demo.py --strategy=DCA_QuotaFromBasePrice   --strategy-args=dca_base_quota=100,dca_base_price=10000         --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromBasePrice_10000.txt
# python bots_demo.py --strategy=DCA_QuotaFromBasePrice   --strategy-args=dca_base_quota=100,dca_base_price=20000         --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromBasePrice_20000.txt
# python bots_demo.py --strategy=DCA_QuotaFromBasePrice   --strategy-args=dca_base_quota=100,dca_base_price=30000         --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromBasePrice_30000.txt
# python bots_demo.py --strategy=DCA_QuotaFromBasePrice   --strategy-args=dca_base_quota=100,dca_base_price=40000         --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromBasePrice_40000.txt
###
# Results for above:
# base=10000 16.5 @ 7400
# base=20000 17.0 @ 7800
# base=30000 17.2 @ 8100
# base=40000 17.3 @ 8300
###


# backtesting MA length
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA --strategy-args=dca_base_quota=100,ma_period=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA --strategy-args=dca_base_quota=100,ma_period=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA --strategy-args=dca_base_quota=100,ma_period=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_100.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA --strategy-args=dca_base_quota=100,ma_period=200 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_200.txt
###
# Results for above:
# Q=200 19.3 @ 7500
# Q=100 18.3 @ 7900
# Q=50 17.7 @ 8150
# Q=20 17.5 @ 8300
###


# backtesting fast MA length
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=5,overprice_filter_ma_length=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_5_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=5,overprice_filter_ma_length=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_5_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=5,overprice_filter_ma_length=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_5_100.txt

# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=20,overprice_filter_ma_length=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_20_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=20,overprice_filter_ma_length=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_20_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=20,overprice_filter_ma_length=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_20_100.txt

# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=50,overprice_filter_ma_length=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_50_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=50,overprice_filter_ma_length=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_50_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=50,overprice_filter_ma_length=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_50_100.txt

# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=100,overprice_filter_ma_length=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_100_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=100,overprice_filter_ma_length=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_100_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=100,overprice_filter_ma_length=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_100_100.txt

# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=200,overprice_filter_ma_length=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_200_20.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=200,overprice_filter_ma_length=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_200_50.txt
# python bots_demo.py --strategy=DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA --strategy-args=dca_base_quota=100,quota_multiplier_ma_length=200,overprice_filter_ma_length=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/DCA_QuotaFromSlowSMA_FilterOverpricedByFastSMA_200_100.txt
###
#Results for above:
# Q = quota multiplier SMA length
# F = overprice filter SMA length
# Q=200 F=100 11.5 @ 6700
# Q=200 F=50 10.8 @ 7000
# Q=100 F=100 10.8 @ 7000
# Q=50 F=100 9.9 @ 7000
# Q=200 F=20 9.5 @ 7300
# Q=20 F=100 9.2 @ 7100
# Q=5 F=100 8.3 @ 7100
# Q=100 F=50 10.4 @ 7400
# Q=50 F=50 9.8 @ 7530
# Q=20 F=50 9.0 @ 7600
# Q=5 F=50 8.6 @ 7600
# Q=100 F=20 9.1 @ 7700
# Q=50 F=20 8.8 @ 7900
# Q=20 F=20 8.4 @ 8060
# Q=5 F=20 7.9 @ 8100
###


# # backtesting remove_percent
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=0.5 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp0.5.txt
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=1 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp1.txt
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=3 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp3.txt
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=5 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp5.txt
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=7 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp7.txt
# python bots_demo.py --strategy=DCA_SellFixedPercentByMacd --strategy-args=remove_percent=9 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp9.txt


#backtesting MACD
# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=True --sym=bitcoin --backtest --account=1000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/macd-1d-l-s.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=False --sym=bitcoin --backtest --account=1000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/macd-1d-l.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=False,shorts=True --sym=bitcoin --backtest --account=1000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/macd-1d-s.txt

# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=True --sym=bitcoin --backtest --account=1000 --tf=4h --start=2019-01-01 --end=2021-09-01 > $reports_dir/macd-4h-l-s.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=False --sym=bitcoin --backtest --account=1000 --tf=4h --start=2019-01-01 --end=2021-09-01 > $reports_dir/macd-4h-l.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=False,shorts=True --sym=bitcoin --backtest --account=1000 --tf=4h --start=2019-01-01 --end=2021-09-01 > $reports_dir/macd-4h-s.txt

# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=True --sym=bitcoin --backtest --account=1000 --tf=1h --start=2021-01-01 --end=2021-09-01 > $reports_dir/macd-1h-l-s.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=True,shorts=False --sym=bitcoin --backtest --account=1000 --tf=1h --start=2021-01-01 --end=2021-09-01 > $reports_dir/macd-1h-l.txt
# python bots_demo.py --strategy=MACD --strategy-args=longs=False,shorts=True --sym=bitcoin --backtest --account=1000 --tf=1h --start=2021-01-01 --end=2021-09-01 > $reports_dir/macd-1h-s.txt

# python bots_demo.py --strategy=MACross --sym=ethereum --backtest --account=1000 --tf=4h --start=2021-03-04 --end=2021-09-04

# python bots_demo.py --strategy=BigMoveDetect --strategy-args=threshold=2 --sym=ethereum --backtest --account=1000 --tf=15m --start=2021-08-01 --end=2021-09-10 > $reports_dir/bigmove.txt

# python bots_demo.py --strategy=FindPeaks --sym=solana --backtest --tf=4h --start=2021-05-01 --end=2021-09-23 > $reports_dir/findpeaks.txt
