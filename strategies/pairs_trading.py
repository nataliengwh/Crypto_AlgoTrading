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
        max_lookback = 30,
        enter_threshold_size = 2,
        exit_threshold_size = 0.5,
        loss_limit = -0.015,
        consider_borrow_cost = False,
        consider_commission = False,
        print_bar = True,
        print_msg = False,
        print_transaction = False,
        coin0 = '',
        coin1 = '',
    )

    ##################################### INIT #####################################

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Pairs Trading strategy")

        # keeps track whether order is pending
        self.orderid = None

        # general info
        self.coin0 = self.p.coin0
        self.coin1 = self.p.coin1

        # Strategy params
        self.lookback = self.p.lookback
        self.max_lookback = self.p.max_lookback
        self.enter_threshold_size = self.p.enter_threshold_size
        self.exit_threshold_size = self.p.exit_threshold_size
        self.loss_limit = self.p.loss_limit
        self.consider_borrow_cost = self.p.consider_borrow_cost
        self.consider_commission = self.p.consider_commission

        # Parameters for printing
        self.print_bar = self.p.print_bar
        self.print_msg = self.p.print_msg
        self.print_transaction = self.p.print_transaction

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
        self.allow_trade = True
        
        # for logging
        self.latest_trade_action = None
        self.sell_stk = None
        self.buy_stk = None
        self.sell_amt = None
        self.buy_amt = None
    
    ##################################### ACTIONS WHEN LIMIT REACHED #####################################
    
    def long_spread(self):
        # Calculating the number of shares for each stock
        x = int((2 * self.broker.getvalue() / 3.0) / (self.data0[0])) 
        y = int((2 * self.broker.getvalue() / 3.0) / (self.data1[0])) 

        # Place the order
        self.buy(data=self.data0, size=(x + self.qty0))  # Place an order for buying x + qty1 shares
        self.sell(data=self.data1, size=(y + self.qty1))  # Place an order for selling y + qty2 shares

        # Updating the counters with new value
        self.qty0 = x 
        self.qty1 = y 

        # update flags
        self.status = 2  

        # keep track of trade variables
        self.initial_cash = self.qty0 * self.data0[0] + 0.5 * self.qty1 * self.data1[0]
        self.initial_long_pv = self.long_portfolio_value(self.qty0, self.data0[0])
        self.initial_short_pv = 0.5 * self.data1[0] * self.qty1
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]

        # logging
        self.latest_trade_action = "long_spread"
        self.sell_stk = self.coin1
        self.buy_stk = self.coin0
        self.sell_amt = y + self.qty1
        self.buy_amt = x + self.qty0

    def short_spread(self):
        x = int((2 * self.broker.getvalue() / 3.0) / (self.data0.close[0]))  
        y = int((2 * self.broker.getvalue() / 3.0) / (self.data1.close[0]))  

        # Placing the order
        self.sell(data=self.data0, size=(x + self.qty0))  # Place an order for buying y + qty2 shares
        self.buy(data=self.data1, size=(y + self.qty1))  # Place an order for selling x + qty1 shares

        # Updating the counters with new value
        self.qty0 = x  
        self.qty1 = y  

        # update flags
        self.status = 1

        # keep track of trade variables
        self.initial_cash = self.qty1 * self.data1[0] + 0.5 * self.qty0 * self.data0[0]
        self.initial_long_pv = self.long_portfolio_value(self.qty1, self.data1[0])
        self.initial_short_pv = 0.5 * self.data0[0] * self.qty0
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]
        
        # logging
        self.latest_trade_action = "short_spread"
        self.sell_stk = self.coin0
        self.buy_stk = self.coin1
        self.sell_amt = x + self.qty0
        self.buy_amt = y + self.qty1

    def exit_spread(self):
        # Exit position
        self.close(self.data0)
        self.close(self.data1)

        # logging
        self.latest_trade_action = "exit_spread"
        self.sell_stk = None
        self.buy_stk = None
        self.sell_amt = None
        self.buy_amt = None

        # update counters
        self.qty0 = 0
        self.qty1 = 0

        # update flags
        self.status = 0
        self.initial_cash = None
        self.initial_long_pv, self.initial_short_pv = None, None
        self.initial_price_data0, self.initial_price_data1 = None, None
    
    def long_portfolio_value(price, qty):
        return price * qty

    def short_portfolio_value(price_initial, price_final, qty):
        return qty * (1.5 * price_initial - price_final)

    ################################# FOR EXECUTIONS #################################
    
    def update_threshold(self):
        # define limits when no position
        Y = pd.Series(self.data0.get(size=self.lookback, ago=1))
        X = pd.Series(self.data1.get(size=self.lookback, ago=1))

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
        # short data0, long data1
        elif self.status == 1:
            if spread < self.lower_limit:
                self.long_spread()
            elif spread < self.up_medium:
                self.exit_spread()

    ##################################### EXECUTE #####################################

    def next(self):
        # reset variable
        self.latest_trade_action = None
        self.sell_stk = None
        self.buy_stk = None
        self.sell_amt = None
        self.buy_amt = None

        if self.status == 0: # no position
            self.update_threshold() # get enter/ exit levels
        if self.allow_trade and (not self.orderid):
            self.run_trade_strategy() 
        if self.print_msg:
            self.log_status()