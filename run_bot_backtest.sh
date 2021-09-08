#python bots_demo.py --strategy=MACross --sym=ethereum --backtest --account=1000 --tf=4h --start=2021-03-04 --end=2021-09-04

# # backtesting MA period
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=0 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period0.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=20 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period20.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=50 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period50.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=100 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period100.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200 --sym=ethereum --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > period200.txt

# # backtesting remove_percent
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=0.5 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp0.5.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=1 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp1.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=3 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp3.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=5 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp5.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=7 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp7.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200,remove_percent=9 --sym=bitcoin --backtest --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > rp9.txt

