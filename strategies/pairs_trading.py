import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase
import pandas as pd
import logging
_logger = logging.getLogger(__name__)

class PairsTrading(StrategyBase):
    ##################################### PARAMS #####################################
    
    params = dict (
        lookback = 20,
        enter_threshold_size = 2,
        exit_threshold_size = 0.5,
        loss_limit = -0.015,
        coin0 = '',
        coin1 = '',
    )

    ##################################### INIT #####################################

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Pairs Trading strategy")

        self.coin0 = self.p.coin0
        self.coin1 = self.p.coin1
        self.lookback = self.p.lookback
        self.enter_threshold_size = self.p.enter_threshold_size
        self.exit_threshold_size = self.p.exit_threshold_size
        self.loss_limit = self.p.loss_limit

        # temporary variables for trading logic
        self.status = 0
        self.qty0 = 0
        self.qty1 = 0
        self.initial_price_data0 = None
        self.initial_price_data1 = None
        self.initial_cash = None
        self.initial_long_pv = None
        self.initial_short_pv = None
        self.upper_limit = None
        self.lower_limit = None
        self.up_medium = None
        self.low_medium = None

    ##################################### ACTIONS WHEN LIMIT REACHED #####################################

    @staticmethod
    def long_portfolio_value(price, qty):
        return price * qty

    @staticmethod
    def short_portfolio_value(price_initial, price_final, qty):
        return qty * (1.5 * price_initial - price_final)

    def long_spread(self):
        self.status = 2
        x = int((2 * self.broker.getvalue() / 3.0) / (self.data0[0]))
        y = int((2 * self.broker.getvalue() / 3.0) / (self.data1[0]))
        self.buy(data=self.data0, size=(x + self.qty0))
        self.sell(data=self.data1, size=(y + self.qty1))
        self.qty0 = x
        self.qty1 = y
        self.initial_cash = self.qty0 * self.data0[0] + 0.5 * self.qty1 * self.data1[0]
        self.initial_long_pv = self.data0[0] * self.qty0
        self.initial_short_pv = 0.5 * self.data1[0] * self.qty1
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]

        print("########### Trade Action: Long spread ###########")
        print(f"         Buy {self.qty0} {self.coin0} @ {self.data0[0]}")
        print(f"         Sell {self.qty1} {self.coin1} @ {self.data1[0]}")

    def short_spread(self):
        self.status = 1
        x = int((2 * self.broker.getvalue() / 3.0) / (self.data0.close[0]))  
        y = int((2 * self.broker.getvalue() / 3.0) / (self.data1.close[0]))
        self.sell(data=self.data0, size=(x + self.qty0))
        self.buy(data=self.data1, size=(y + self.qty1))
        self.qty0 = x  
        self.qty1 = y
        self.initial_cash = self.qty1 * self.data1[0] + 0.5 * self.qty0 * self.data0[0]
        self.initial_long_pv = self.data1[0] * self.qty1
        self.initial_short_pv = 0.5 * self.data0[0] * self.qty0
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]

        print("########### Trade Action: Short spread ###########")
        print(f"         Buy {y + self.qty1} {self.coin1} @ {self.data1[0]}")
        print(f"         Sell {x + self.qty0} {self.coin0} @ {self.data0[0]}")

    def exit_spread(self):
        self.close(self.data0)
        self.close(self.data1)
        self.qty0 = 0
        self.qty1 = 0
        self.status = 0
        self.initial_cash = None
        self.initial_long_pv, self.initial_short_pv = None, None
        self.initial_price_data0, self.initial_price_data1 = None, None

    ################################# FOR EXECUTIONS #################################
    
    def update_threshold(self):
        # define limits when no position
        Y = pd.Series(self.data0.get(size=self.lookback, ago=1),dtype='float64')
        X = pd.Series(self.data1.get(size=self.lookback, ago=1),dtype='float64')
        self.spread_mean = (Y - X).mean()
        self.spread_std = (Y - X).std()
        self.upper_limit = self.spread_mean + self.enter_threshold_size * self.spread_std
        self.lower_limit = self.spread_mean - self.enter_threshold_size * self.spread_std
        self.up_medium = self.spread_mean + self.exit_threshold_size * self.spread_std
        self.low_medium = self.spread_mean - self.exit_threshold_size * self.spread_std

    def run_trade_strategy(self):
        # define actions when limit reach
        spread = (self.data0[0] - self.data1[0])
        # no position
        if self.status == 0:
            if spread > self.upper_limit:
                self.short_spread()
            elif spread < self.lower_limit:
                self.long_spread()
        elif self.status == 1:
            # short coin0, long coin1
            if spread < self.lower_limit:
                self.long_spread()
            elif spread < self.up_medium:
                self.exit_spread()
            else:
                long_pv = self.long_portfolio_value(self.data1[0], self.qty1)
                short_pv = self.short_portfolio_value(self.initial_price_data0, self.data0[0], self.qty0)
                net_gain_long = long_pv - self.initial_long_pv
                net_gain_short = short_pv - self.initial_short_pv
                return_of_current_trade = (net_gain_long + net_gain_short) / self.initial_cash
                if return_of_current_trade < self.loss_limit or short_pv <= 0:
                    self.exit_spread()
        elif self.status == 2:
            # long coin0, short coin1
            if spread > self.upper_limit:
                self.short_spread()
            elif spread > self.low_medium:
                self.exit_spread()
            else:
                long_pv = self.long_portfolio_value(self.data0[0], self.qty0)
                short_pv = self.short_portfolio_value(self.initial_price_data1, self.data1[0], self.qty1)
                net_gain_long = long_pv - self.initial_long_pv
                net_gain_short = short_pv - self.initial_short_pv
                return_of_current_trade = (net_gain_long + net_gain_short) / self.initial_cash
                if return_of_current_trade < self.loss_limit or short_pv <= 0:
                    self.exit_spread()

    ##################################### EXECUTE #####################################

    def next(self):
        if self.status == 0: # no position
            self.update_threshold() # get enter/ exit levels
        self.run_trade_strategy()