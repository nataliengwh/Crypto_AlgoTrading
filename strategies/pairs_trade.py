from strategies.base import StrategyBase
import pandas as pd

import logging
_logger = logging.getLogger(__name__)

class PairsTrade(StrategyBase):

    params = dict(
        lookback=20,
        enter_std=2,
        exit_std=1, #0.5
        stop_loss=-0.05, #-0.015
        coin0='',
        coin1='',
        )

    ##################################### INIT #####################################

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Pairs Trading strategy")
        self.lookback = self.p.lookback
        self.enter_std = self.p.enter_std
        self.exit_std = self.p.exit_std
        self.stop_loss = self.p.stop_loss
        self.coin0 = self.p.coin0
        self.coin1 = self.p.coin1
        self.status = "no_position"
        self.qty0, self.qty1 = 0, 0
        self.enter_upper, self.enter_lower = None, None
        self.exit_upper, self.exit_lower = None, None

    def get_threshold(self, spread):
        # calculate enter and exit entry point
        S0 = pd.Series(self.data0.get(size=self.lookback,ago=1),dtype='float64')
        S1 = pd.Series(self.data1.get(size=self.lookback, ago=1),dtype='float64')
        mean = (S0 - S1).mean()
        std = (S0 - S1).std()
        self.enter_upper = mean + (self.enter_std * std)
        self.enter_lower = mean - (self.enter_std * std)
        self.exit_upper = mean + (self.exit_std * std)
        self.exit_lower = mean - (self.exit_std * std)

        if spread > self.enter_upper:
            # indicates that cn0 is overpriced
            self.short_coin0()
        elif spread < self.enter_upper:
            # indicates that cn1 is overpriced
            self.long_coin0()

    def long_coin0(self):
        self.status = 'long_coin0'
        self.qty0 = round(self.broker.getvalue() / 2 / self.data0[0],2) # round FOR BTC
        self.qty1 = int(self.broker.getvalue() / 2 / self.data1[0])
        self.buy(data=self.data0,size=(self.qty0))
        self.sell(data=self.data1, size=(self.qty1))
        print(f"##################### Long {self.coin0} #####################")
        print(f"Long {self.qty0} {self.coin0} @ {self.data0[0]}")
        print(f"Short {self.qty1} {self.coin1} @ {self.data1[0]}")

    def short_coin0(self):
        self.status = 'short_coin0'
        self.qty0 = round(self.broker.getvalue() / 2 / self.data0[0],2)
        self.qty1 = int(self.broker.getvalue() / 2 / self.data1[0])
        self.sell(data=self.data0, size=(self.qty0))
        self.buy(data=self.data1, size=(self.qty1))
        print(f"##################### Short {self.coin0} #####################")
        print(f"Short {self.qty0} {self.coin0} @ {self.data0[0]}")
        print(f"Long {self.qty1} {self.coin1} @ {self.data1[0]}")

    def exit_trade(self):
        self.status = 'no_position'
        self.close(self.data0)
        self.close(self.data1)
        self.qty0, self.qty1 = 0, 0

    ##################################### EXECUTE #####################################

    def next(self):
        spread = (self.data0[0] - self.data1[0])
        if self.status == 'no_position':
            self.get_threshold(spread)

        elif ((self.status == 'long_coin0') & (spread > self.exit_lower)) | \
                ((self.status == 'short_coin0') & (spread < self.exit_upper)):
            if self.status == 'long_coin0':
                print(f"exit long_coin0   -     {spread}   -     {self.exit_lower}")
            elif self.status == 'short_coin0':
                print(f"exit short_coin0   -    {spread}   -    {self.exit_upper}")
            self.exit_trade()
