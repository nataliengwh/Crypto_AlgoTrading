import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase

class SMA_3_lines(StrategyBase):
    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using 3 SMA strategy")

        self.sma_fast = bt.indicators.MovingAverageSimple(self.data0.close, period = 20)
        self.sma_mid = bt.indicators.MovingAverageSimple(self.data0.close, period = 60)
        self.sma_slow = bt.indicators.MovingAverageSimple(self.data0.close, period = 200)
        self.profit_treshold = 0
        self.profit = 0
        self.max_profit = 0


    def next(self):
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        if self.last_operation != "BUY":
            if self.sma_fast > self.sma_slow and self.sma_mid > self.sma_slow:
                self.log("Long by indicator golden cross: percentage %.5f %%" % self.profit)
                self.long()               
            
        if self.last_operation != "SELL":
            if self.sma_fast < self.sma_slow and self.sma_mid < self.sma_slow:
                self.log("Short by indicator death cross: percentage %.5f %%" % self.profit)
                self.short()
