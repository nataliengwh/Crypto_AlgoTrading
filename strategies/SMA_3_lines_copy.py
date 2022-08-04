import backtrader as bt
from datetime import datetime
from termcolor import colored

class SMA_3_lines(bt.Strategy):

    def __init__(self):
        self.log("Using 3 SMA strategy")

        self.sma_fast = bt.indicators.MovingAverageSimple(self.data0.close, period = 100)
        self.sma_mid = bt.indicators.MovingAverageSimple(self.data0.close, period = 400)
        self.sma_slow = bt.indicators.MovingAverageSimple(self.data0.close, period = 800)
        
        #self.signal_1 = bt.indicators.CrossOver(self.sma_fast, self.sma_mid)
        self.signal_2 = bt.indicators.CrossOver(self.sma_mid, self.sma_slow)
        self.signal_2.plotinfo.plot = False

    def log(self, txt, send_telegram=False, color=None):
        value = datetime.now()
        if len(self) > 0:
            print(self.data0)
            value = self.data0.datetime.datetime()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))

    def next(self):

        if not self.position and self.sma_fast[0] > self.sma_mid[0] and self.signal_2 == 1:
            self.order = self.buy()

        if self.getposition().size < 0 and self.sma_fast[0] > self.sma_mid[0] and self.signal_2 == 1:
            self.order = self.close()
            self.order = self.buy()

        if not self.position and self.sma_fast[0] < self.sma_mid[0] and self.signal_2 == -1:
            self.order = self.sell() 

        if self.getposition().size > 0 and self.sma_fast[0] < self.sma_mid[0] and self.signal_2 == -1:
            self.order = self.close()
            self.order = self.sell()


        