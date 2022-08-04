import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase

class RSI(StrategyBase):
    params = dict(
        period_ema_fast=20, #10
        period_ema_slow=50 #100
    )

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using RSI/EMA strategy")

        self.ema_fast = bt.indicators.EMA(period=self.p.period_ema_fast)
        self.ema_slow = bt.indicators.EMA(period=self.p.period_ema_slow)
        self.rsi = bt.indicators.RelativeStrengthIndex()
        self.profit_treshold = 0
        self.profit = 0
        self.max_profit = 0

    def update_indicators(self):
        self.profit = 0
        if self.buy_price_close and self.buy_price_close > 0:
            self.profit = float(self.data0.close[0] - self.buy_price_close) / self.buy_price_close
            if self.profit > self.max_profit:
                self.max_profit = self.profit

    def next(self):
        self.update_indicators()

        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        if self.last_operation != "BUY":
            if self.rsi < 30 and self.ema_fast > self.ema_slow:
                self.log("Long by indicator rsi < 30: percentage %.5f %%" % self.profit)
                self.long()

        if self.last_operation != "SELL":
            # set profit treshhold for stop win
            if self.profit > self.profit_treshold + 0.1:
                self.profit_treshold += 0.1

            # stoploss and stopwin
            if self.profit < -0.05: #0.05
                self.log("STOP LOSS: percentage %.5f %%" % self.profit)
                self.log("MAX PROFIT: percentage %.5f %%" % self.max_profit)
                self.profit_treshold = 0
                self.max_profit = 0
                self.short()
            elif self.profit < self.max_profit - 0.05: #profit_treshold
                self.log("STOP WIN: percentage %.5f %%" % self.profit)
                self.log("MAX PROFIT: percentage %.5f %%" % self.max_profit)
                self.max_profit = 0
                self.profit_treshold = 0
                self.short()
