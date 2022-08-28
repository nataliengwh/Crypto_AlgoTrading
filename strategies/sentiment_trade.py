import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase



class SentimentTrade(StrategyBase):
    params = dict(
        period_ema_fast=20, #10
        period_ema_slow=50 #100
    )

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Sentiment Analysis Results")
        print(dir(self))
        self.profit_treshold = 0
        self.profit = 0
        self.max_profit = 0

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
        
        # self.update_indicators()
        #print(
        #    'C',self.data0._name,
        #    'A',self.data0.datetime[0],
        #    'A',self.data0.close[0],
        #    'C',self.data1._name,
        #    'B',self.data1.datetime[0],
        #    'B',self.data1.sentiment_flair[0],
        #    'B',self.data1.sentiment_vadar[0],
        #    'B',self.data1.sentiment_transformer[0],
        #    )
        
        
        
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        if self.order:  # waiting for pending order
            return

        if self.last_operation != "BUY":
            if self.data1.sentiment_vadar[0]<0.1:
                self.log("Long by positive market sentiment: percentage %.5f %%" % self.profit)
                self.long()               
            
        if self.last_operation != "SELL":
            if self.data1.sentiment_vadar[0]>0.9:
                self.log("Short by negative market sentiment: percentage %.5f %%" % self.profit)
                self.short()

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