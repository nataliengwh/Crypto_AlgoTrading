import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase



class SentimentTrade(StrategyBase):
    params = dict(
        sig=0,
        mode=0, #0/1 momentum/constraian
        which_sentiment=0, #0/1/2 for flair/vadar/trasnformer
        sent_neg_threshold = 0.2,
        sent_pos_threshold = 0.8,
        period_ema_fast=20, #10
        period_ema_slow=50, #100
        period_sma_fast=20, #10
        period_sma_slow=50, #100
    )

    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using Sentiment Analysis Results")
        #print(dir(self))

        if self.p.which_sentiment == 0:
            self.sentiment_value = self.data1.sentiment_flair
        elif self.p.which_sentiment == 1:
            self.sentiment_value = self.data1.sentiment_vadar
        elif self.p.which_sentiment == 2:
            self.sentiment_value = self.data1.sentiment_transformer
        self.sma_fast = bt.indicators.MovingAverageSimple(self.sentiment_value, period = self.p.period_sma_fast)
        self.sma_slow = bt.indicators.MovingAverageSimple(self.sentiment_value, period = self.p.period_sma_fast)
        self.ema_fast = bt.indicators.EMA(self.sentiment_value, period=self.p.period_ema_fast)
        self.ema_slow = bt.indicators.EMA(self.sentiment_value, period=self.p.period_ema_slow)
        self.rsi = bt.indicators.RelativeStrengthIndex()

        self.profit_treshold = 0
        self.profit = 0
        self.max_profit = 0

    def update_indicators(self):
        self.profit = 0
        if self.buy_price_close and self.buy_price_close > 0:
            self.profit = float(self.data.close[0] - self.buy_price_close) / self.buy_price_close
            if self.profit > self.max_profit:
                self.max_profit = self.profit

    def next(self):
        
        self.update_indicators()
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
        #print(self.sma_fast[0])
        
        
        
        if self.status != "LIVE" and ENV == PRODUCTION:  # waiting for live status in production
            return

        
        if self.order:  # waiting for pending order
            return
        
        if self.p.sig==0:
            if self.p.mode==0:#0/1 momentum/constraian
                if self.last_operation != "BUY":
                    if self.sma_fast[0] > self.p.sent_pos_threshold:
                        #print(self.last_operation)
                        self.log("Long by positive market sentiment: percentage %.5f %%" % self.profit)
                        self.long()               
                    
                if self.last_operation != "SELL":
                    if self.sma_fast[0] < self.p.sent_neg_threshold:
                        #print(self.last_operation)
                        self.log("Short by negative market sentiment: percentage %.5f %%" % self.profit)
                        self.short()
            if self.p.mode==1:#0/1 momentum/constraian
                if self.last_operation != "SELL":
                    if self.sma_fast[0] > self.p.sent_pos_threshold:
                        #print(self.last_operation)
                        self.log("short by positive market sentiment: percentage %.5f %%" % self.profit)
                        self.short()               
                    
                if self.last_operation != "BUY":
                    if self.sma_fast[0] < self.p.sent_neg_threshold:
                        #print(self.last_operation)
                        self.log("Long by negative market sentiment: percentage %.5f %%" % self.profit)
                        self.long()
        if self.p.sig==1:
            if self.p.mode==0:#0/1 momentum/constraian
                if self.last_operation != "BUY":
                    if self.ema_fast[0] > self.p.sent_pos_threshold:
                        #print(self.last_operation)
                        self.log("Long by positive market sentiment: percentage %.5f %%" % self.profit)
                        self.long()               
                    
                if self.last_operation != "SELL":
                    if self.ema_fast[0] < self.p.sent_neg_threshold:
                        #print(self.last_operation)
                        self.log("Short by negative market sentiment: percentage %.5f %%" % self.profit)
                        self.short()
            if self.p.mode==1:#0/1 momentum/constraian
                if self.last_operation != "SELL":
                    if self.ema_fast[0] > self.p.sent_pos_threshold:
                        #print(self.last_operation)
                        self.log("short by positive market sentiment: percentage %.5f %%" % self.profit)
                        self.short()               
                    
                if self.last_operation != "BUY":
                    if self.ema_fast[0] < self.p.sent_neg_threshold:
                        #print(self.last_operation)
                        self.log("Long by negative market sentiment: percentage %.5f %%" % self.profit)
                        self.long()
