import backtrader as bt
import numpy as np
import datetime

class GridStrategy(bt.Strategy):

    params = (('grids',10), ('width',0.01))

    def __init__(self):


        # self.highest = bt.indicators.Highest(self.data.high, period=self.p.period, subplot=False)
        # self.lowest = bt.indicators.Lowest(self.data.low, period=self.p.period, subplot=False)
        # mid = (self.highest + self.lowest)/2
        # mid = self.data[0]
        # # mid = 20000
        # perc_levels = [x for x in np.arange(
        #         1 + self.p.width * 5,
        #         1 - self.p.width * 5- self.p.width/2,
        #         -self.p.width)]
        # self.price_levels = [mid * x for x in perc_levels]
        self.last_price_index = None
        
    def prenext(self):
        mid = self.data0.close[0]
        perc_levels = [x for x in np.arange(
                1 + self.p.width * self.p.grids/2,
                1 - self.p.width * self.p.grids/2- self.p.width/2,
                -self.p.width)]
        self.price_levels = [mid * x for x in perc_levels]
        
    def next(self):
        if self.data.datetime.datetime().month != self.data.datetime.datetime(ago = -1).month:
            # print(self.data.datetime.datetime().month)
            # print(self.data0.close[0])
            mid = self.data0.close[0]
            perc_levels = [x for x in np.arange(
                    1 + self.p.width * self.p.grids/2,
                    1 - self.p.width * self.p.grids/2-self.p.width/2,
                    -self.p.width)]
            self.price_levels = [mid * x for x in perc_levels]
            # self.last_price_index = None
            return    

        elif self.last_price_index == None:
            for i in range(len(self.price_levels)):
                if self.data.close > self.price_levels[i]:
                    self.last_price_index = i
                    self.order_target_percent(
                        target=i/(len(self.price_levels) - 1))
                    return
        else:
            signal = False
            while True:
                upper = None
                lower = None
                if self.last_price_index > 0:
                    upper = self.price_levels[self.last_price_index - 1]
                if self.last_price_index < len(self.price_levels) - 1:
                    lower = self.price_levels[self.last_price_index + 1]

                if upper != None and self.data.close > upper:
                    self.last_price_index = self.last_price_index - 1
                    signal = True
                    continue

                if lower != None and self.data.close < lower:
                    self.last_price_index = self.last_price_index + 1
                    signal = True
                    continue
                break
            if signal:
                self.long_short = None
                self.order_target_percent(
                    target=self.last_price_index/(len(self.price_levels) - 1))

    # def next(self):
    #     if self.last_price_index == None:
    #         for i in range(len(self.price_levels)):
    #             if self.data.close > self.price_levels[i]:
    #                 self.last_price_index = i
    #                 self.order_target_percent(
    #                     target=i/(len(self.price_levels) - 1))
    #                 return
    #     else:
    #         signal = False
    #         while True:
    #             upper = None
    #             lower = None
    #             if self.last_price_index > 0:
    #                 upper = self.price_levels[self.last_price_index - 1]
    #             if self.last_price_index < len(self.price_levels) - 1:
    #                 lower = self.price_levels[self.last_price_index + 1]

    #             if upper != None and self.data.close > upper:
    #                 self.last_price_index = self.last_price_index - 1
    #                 signal = True
    #                 continue

    #             if lower != None and self.data.close < lower:
    #                 self.last_price_index = self.last_price_index + 1
    #                 signal = True
    #                 continue
    #             break
    #         if signal:
    #             self.long_short = None
    #             self.order_target_percent(
    #                 target=self.last_price_index/(len(self.price_levels) - 1))

    def stop(self):
        print('grids: %s, width: %s, final value: %.2f' %(
            self.p.grids, self.p.width, self.broker.getvalue()
        ))