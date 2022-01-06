import argparse, yaml, time
from typing import Any
from collections import defaultdict
from math import isclose
from pandas.core.frame import DataFrame
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


from lib.common.msg import *
from lib.common.market_data import MarketData
from lib.common.id_ticker_map import id_to_ticker
from lib.trader import api_keys_config
from lib.trader import ftx_api
from lib.defi.solscan_api import Solscan
from lib.common.sound_notification import VoiceNotification

conf: dict[str, Any] = {}


def reread_conf():
    global conf
    conf = yaml.safe_load(open('config/tulipgarden.yml', 'r'))


class FtxClient:
    def __init__(self):
        cfg = api_keys_config.ApiKeysConfig()
        self._api = ftx_api.Ftx(cfg.get_ftx_ks()[0], cfg.get_ftx_ks()[1], cfg.get_ftx_subaccount_tuliphedgedshorts())

    def get_account_value(self):
        return sum([x['usdValue'] for x in self.balances]) + sum([x['unrealizedPnl'] for x in self.positions])

    def get_positions_pnl(self):
        pnl = {}
        for p in self.positions:
            if not isclose(p['netSize'], 0):
                pnl[p['future'].replace('-PERP','')] = p['recentPnl']
        return pnl

    @property
    def account(self):
        return self._api.get_account_information()

    @property
    def positions(self):
        return self._api.get_positions()

    @property
    def balances(self):
        return self._api.get_balances()


class TulipClient:
    def __init__(self):
        options = webdriver.ChromeOptions()
        options.add_argument("user-data-dir=cache/tulipgarden/selenium")
        options.add_extension("data/tulipgarden/Phantom.crx")
        self._driver = webdriver.Chrome(options=options)
        self._driver.get("https://tulip.garden/your-positions")

    def get_lyf_positions(self):
        d =[]
        for e in WebDriverWait(self._driver,60).until(EC.presence_of_all_elements_located((By.CLASS_NAME, "your-positions-table__row-item"))):
            data_cols = e.find_elements_by_class_name("your-positions-table__row-item__cell")
            lp_name = e.find_element_by_class_name("your-positions-table__row-item__asset__text-name").text
            debt_value_container = data_cols[1].find_elements_by_class_name("position-breakup__item")
            #print("debt_value_container", debt_value_container)
            debt_value_token = debt_value_container[0].find_element_by_class_name("position-breakup__item-value").text
            #print("debt_value_token", debt_value_token)
            debt_value_stable = debt_value_container[1].find_element_by_class_name("position-breakup__item-value").text
            #print("debt_value_stable", debt_value_stable)
            equity_value = data_cols[2].find_element_by_xpath("./div").text
            kill_buffer = data_cols[3].find_element_by_xpath("./div").text
            
            d.append({
                'LP': lp_name,
                'tulip_equity_value': float(equity_value.replace("$","").replace(",","").strip()),
                'tulip_kill_buffer': float(kill_buffer.replace("%","").replace(",","").strip()),
                'tulip_debt_value_token': float(debt_value_token.replace(",","").strip()),
                'tulip_debt_value_stable': float(debt_value_stable.replace(",","").strip()),
            })
        #print(DataFrame.from_dict(d).to_string())
        return d


class MarketPriceClient:
    def __init__(self):
        self._market_data = MarketData()

    def get_token_price(self, ticker: str):
        token_id = [k for k,v in id_to_ticker.items() if v == ticker][0]
        return self._market_data.get_market_price(token_id)

 
def get_main_token_of_liquidity_pair(lp):
    return lp.replace("LP","").replace("-USDT","").replace("-USDC","").replace("we","").strip()


class CmdListPositions:
    def __init__(self):
        self.ftx = FtxClient()
        self.tulip = TulipClient()
        self.solscan = Solscan(conf['lyf_account'])

    def do_action(self):
        reread_conf()

        tulip = self.tulip
        ftx = self.ftx
        solscan = self.solscan
        market_price = MarketPriceClient()

        tulip_lyf_positions = tulip.get_lyf_positions()

        # long positions that are short-hedged on FTX
        ftx_hedged_short_positions_pnl = ftx.get_positions_pnl()

        tulip_lyf_positions_ftx_hedged= []
        tulip_lyf_positions_self_hedged = []

        for x in tulip_lyf_positions:
            main_token_of_lp = get_main_token_of_liquidity_pair(x['LP'])
            xx = x
            xx['current_price'] = market_price.get_token_price(main_token_of_lp)
            if main_token_of_lp in ftx_hedged_short_positions_pnl:
                tulip_lyf_positions_ftx_hedged.append(xx)
            else:
                tulip_lyf_positions_self_hedged.append(xx)



        print()
        print("Positions:")
        print()
        print("Neutral / FTX hedged")
        print()
        

        df_tulip_long_lyf_positions = DataFrame.from_dict(tulip_lyf_positions_ftx_hedged)
        if df_tulip_long_lyf_positions.size > 0:
            df_tulip_long_lyf_positions['ftx_hedged_short_pnl'] = [ ftx_hedged_short_positions_pnl[ get_main_token_of_liquidity_pair(x) ]  for x in df_tulip_long_lyf_positions['LP']]
            df_tulip_long_lyf_positions['ftx_kill_buffer'] = (ftx.account['marginFraction'] - ftx.account['maintenanceMarginRequirement'])*100 
            df_tulip_long_lyf_positions['tulip_equity_value'] = df_tulip_long_lyf_positions['tulip_equity_value'] + df_tulip_long_lyf_positions['ftx_hedged_short_pnl']
            df_tulip_long_lyf_positions['pnl'] = df_tulip_long_lyf_positions['tulip_equity_value'] -  [ conf['lyf_position_entry_value'][x] for x in df_tulip_long_lyf_positions['LP'] ]
            print(df_tulip_long_lyf_positions.sort_values('LP').to_string(index=False))
            print()


        print()
        print("Neutral / self hedged")
        print()
    
        df_tulip_neutral_lyf_positions = DataFrame.from_dict(tulip_lyf_positions_self_hedged)
        if df_tulip_neutral_lyf_positions.size > 0:
            df_tulip_neutral_lyf_positions['debt_skew'] =round( df_tulip_neutral_lyf_positions['tulip_debt_value_token'] / 3 * df_tulip_neutral_lyf_positions['current_price'] /  df_tulip_neutral_lyf_positions['tulip_debt_value_stable'], 2)
            df_tulip_neutral_lyf_positions['pnl'] = df_tulip_neutral_lyf_positions['tulip_equity_value'] - [ conf['lyf_position_entry_value'][x] for x in df_tulip_neutral_lyf_positions['LP'] ]
            print(df_tulip_neutral_lyf_positions.sort_values('LP').to_string(index=False))

            skew_thr = conf['debt_skew_threshold_percent']
            unbalanced_list =[]
            for i,x in df_tulip_neutral_lyf_positions.iterrows():
                if x['debt_skew'] > 1+(skew_thr*0.01) or x['debt_skew'] < 1-(skew_thr*0.01):
                    if x['debt_skew']  > 1: # need to borrow more stable
                        need_borrow_stable = x['tulip_debt_value_token'] / 3 * x['current_price']  - x['tulip_debt_value_stable']
                        if need_borrow_stable > 15:
                            print(f"{x['LP']}: debt unbalanced: you need to borrow {round(need_borrow_stable,2)} more USDC")
                            unbalanced_list.append(x['LP'])
                    elif x['debt_skew']  < 1: # need to borrow more unstable
                        need_borrow_unstable = x['tulip_debt_value_stable'] / x['current_price'] - x['tulip_debt_value_token'] / 3
                        if need_borrow_unstable * x['current_price'] > 15:
                            print(f"{x['LP']}: debt unbalanced: you need to borrow {round(need_borrow_unstable,6)} more {get_main_token_of_liquidity_pair(x['LP'])}")
                            unbalanced_list.append(x['LP'])
            if len(unbalanced_list) > 0:
                VoiceNotification().say(f"tulip {', '.join(unbalanced_list)} debt is unbalanced")
       

        lyf_account_stablecoins_balance = solscan.get_token_qty('USDC') + solscan.get_token_qty('USDT')

        accounts_value  = 0
        if  df_tulip_long_lyf_positions.size > 0:
            accounts_value += df_tulip_long_lyf_positions['tulip_equity_value'].sum()
        if df_tulip_neutral_lyf_positions.size > 0:
            accounts_value += df_tulip_neutral_lyf_positions['tulip_equity_value'].sum()

        accounts_value += lyf_account_stablecoins_balance + ftx.get_account_value()
        print()
        print(f"Combined Accounts Value: {accounts_value:.2f} USD")
        print(f"FTX Free Collateral:     {ftx.account['freeCollateral']:.2f} USD")
        print()



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--list',action='store_const', const='True', help='display LYF and hedged positions')
    args = parser.parse_args()

    reread_conf()

    if args.list:
        cmd = CmdListPositions()

        while True:
            try:
                cmd.do_action()
                time.sleep(60)
            except Exception as e:
                print(f"unexpected: {e}")
                time.sleep(1)


if __name__ == '__main__':
    main()
