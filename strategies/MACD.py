import backtrader as bt
from config import ENV, PRODUCTION
from strategies.base import StrategyBase

class MACD(StrategyBase):
    params = (
        # Standard MACD Parameters
        ('macd1', 12),
        ('macd2', 26),
        ('macdsig', 9),
        ('atrperiod', 14),  # ATR Period (standard)
        ('atrdist', 3.0),   # ATR distance for stop price
        ('smaperiod', 30),  # SMA Period (pretty standard)
        ('dirperiod', 10),  # Lookback period to consider SMA trend direction
    )




    def __init__(self):
        StrategyBase.__init__(self)
        self.log("Using MACD strategy")
        self.macd = bt.indicators.MACD(self.data1,
                                       period_me1=self.p.macd1,
                                       period_me2=self.p.macd2,
                                       period_signal=self.p.macdsig)

        # Cross of macd.macd and macd.signal
        self.mcross = bt.indicators.CrossOver(self.macd.macd, self.macd.signal)

        # To set the stop price
        self.atr = bt.indicators.ATR(self.data1, period=self.p.atrperiod)

        # Control market trend
        self.sma = bt.indicators.SMA(self.data1, period=self.p.smaperiod)
        self.smadir = self.sma - self.sma(-self.p.dirperiod)


        self.profit_treshold = 0
        self.profit = 0
        self.max_profit = 0

    # def update_indicators(self):
    #     self.profit = 0
    #     if self.buy_price_close and self.buy_price_close > 0:
    #         self.profit = float(self.data0.close[0] - self.buy_price_close) / self.buy_price_close
    #         if self.profit > self.max_profit:
    #             self.max_profit = self.profit


    def next(self):
        if self.order:
            return  # pending order execution

        if not self.position:  # not in the market
            if self.mcross[0] > 0.0 and self.smadir < 0.0:
                self.order = self.buy()
                pdist = self.atr[0] * self.p.atrdist
                self.pstop = self.data.close[0] - pdist

        else:  # in the market
            pclose = self.data.close[0]
            pstop = self.pstop

            if pclose < pstop:
                self.close()  # stop met - get out
            else:
                pdist = self.atr[0] * self.p.atrdist
                # Update only if greater than
                self.pstop = max(pstop, pclose - pdist)




    #     if self.last_operation != "SELL":
    #         # set profit treshhold for stop win
    #         if self.profit > self.profit_treshold + 0.1:
    #             self.profit_treshold += 0.1

    #         # stoploss and stopwin
    #         if self.profit < -0.05: #0.05
    #             self.log("STOP LOSS: percentage %.5f %%" % self.profit)
    #             self.log("MAX PROFIT: percentage %.5f %%" % self.max_profit)
    #             self.profit_treshold = 0
    #             self.max_profit = 0
    #             self.short()
    #         elif self.profit < self.max_profit - 0.05: #profit_treshold
    #             self.log("STOP WIN: percentage %.5f %%" % self.profit)
    #             self.log("MAX PROFIT: percentage %.5f %%" % self.max_profit)
    #             self.max_profit = 0
    #             self.profit_treshold = 0
    #             self.short()
