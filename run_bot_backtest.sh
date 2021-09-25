reports_dir="reports"
[ ! -d "$reports_dir" ] && mkdir "$reports_dir"

#python bots_demo.py --strategy=MACross --sym=ethereum --backtest --account=1000 --tf=4h --start=2021-03-04 --end=2021-09-04


#python bots_demo.py --strategy=DCAQuota --strategy-args=dca_base_quota=100                                  --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2021-01-01 --end=2021-09-20 > $reports_dir/dcaquota1.txt
#python bots_demo.py --strategy=DCAQuotaMult --strategy-args=dca_base_quota=100,dca_base_price=28000         --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2021-01-01 --end=2021-09-20 > $reports_dir/dcaquotamult.txt
#python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200        --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2021-01-01 --end=2021-09-21 > $reports_dir/dcaquotamultma200d.txt
python bots_demo.py --strategy=DCAQuotaToken --strategy-args=dca_base_quota=0.002                           --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2021-01-01 --end=2021-09-20 > $reports_dir/dcaquotatoken1.txt
python bots_demo.py --strategy=DCAQuotaTokenMult --strategy-args=dca_base_quota=0.002,dca_base_price=28000  --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2021-01-01 --end=2021-09-20 > $reports_dir/dcaquotatokenmult.txt

# backtesting MA period
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=0 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/0_period0.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/0_period20.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/0_period50.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/0_period100.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriod --strategy-args=dca_base_quota=100,ma_period=200 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/0_period200.txt



# python bots_demo.py --strategy=DCAQuotaMultMAPeriodOnlyDips --strategy-args=dca_base_quota=200,ma_period=0 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/period0.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriodOnlyDips --strategy-args=dca_base_quota=200,ma_period=20 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/period20.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriodOnlyDips --strategy-args=dca_base_quota=200,ma_period=50 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/period50.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriodOnlyDips --strategy-args=dca_base_quota=200,ma_period=100 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/period100.txt
# python bots_demo.py --strategy=DCAQuotaMultMAPeriodOnlyDips --strategy-args=dca_base_quota=200,ma_period=200 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/period200.txt


# # backtesting remove_percent
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=0.5 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp0.5.txt
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=1 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp1.txt
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=3 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp3.txt
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=5 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp5.txt
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=7 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp7.txt
# python bots_demo.py --strategy=DCASellFixedPercentByMacd --strategy-args=remove_percent=9 --sym=bitcoin --backtest --pnl --account=1000000 --tf=1d --start=2017-09-01 --end=2021-09-01 > $reports_dir/rp9.txt


