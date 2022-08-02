import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase
import pandas as pd
import logging
_logger = logging.getLogger(__name__)

class Pairs_Trading(StrategyBase):
    params = dict(
        
    )

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Pairs Trading strategy")

        # keeps track whether order is pending
        self.orderid = None

        # general info
        self.stk0_symbol = self.p.stk0_symbol
        self.stk1_symbol = self.p.stk1_symbol

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

    def update_threshold(self):
        Y = pd.Series(self.data0.get(size=self.lookback, ago=1))
        X = pd.Series(self.data1.get(size=self.lookback, ago=1))

        self.spread_mean = (Y - X).mean()
        self.spread_std = (Y - X).std()

        self.upper_limit = self.spread_mean + self.enter_threshold_size * self.spread_std
        self.lower_limit = self.spread_mean - self.enter_threshold_size * self.spread_std
        self.up_medium = self.spread_mean + self.exit_threshold_size * self.spread_std
        self.low_medium = self.spread_mean - self.exit_threshold_size * self.spread_std
    
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
        self.initial_long_pv = PTStrategy.long_portfolio_value(self.qty1, self.data1[0])
        self.initial_short_pv = 0.5 * self.data0[0] * self.qty0
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]
        
        # logging
        self.latest_trade_action = "short_spread"
        self.sell_stk = self.stk0_symbol
        self.buy_stk = self.stk1_symbol
        self.sell_amt = x + self.qty0
        self.buy_amt = y + self.qty1
    
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
        self.initial_long_pv = PTStrategy.long_portfolio_value(self.qty0, self.data0[0])
        self.initial_short_pv = 0.5 * self.data1[0] * self.qty1
        self.initial_price_data0, self.initial_price_data1 = self.data0[0], self.data1[0]

        # logging
        self.latest_trade_action = "long_spread"
        self.sell_stk = self.stk1_symbol
        self.buy_stk = self.stk0_symbol
        self.sell_amt = y + self.qty1
        self.buy_amt = x + self.qty0
    
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
    
    def get_spread(self):
        spread = (self.data0[0] - self.data1[0])
        return spread
    
    def run_trade_strategy(self):
        spread = self.get_spread()
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


    def next(self):
        # reset variable
        self.latest_trade_action = None
        self.sell_stk = None
        self.buy_stk = None
        self.sell_amt = None
        self.buy_amt = None

        if self.status == 0: # no position
            self.update_threshold()
        
        if self.allow_trade and (not self.orderid):
            self.run_trade_strategy()

        ###################################################################################
        # STRATEGY LOGIC                                                                  #
        ###################################################################################
        # if an order is active, no new orders are allowed
        if self.allow_trade and (not self.orderid):
            self.run_trade_logic()

        if self.print_msg:
            self.log_status()