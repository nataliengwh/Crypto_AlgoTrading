from sqlite3 import paramstyle
import backtrader as bt
from datetime import datetime
from termcolor import colored

class SMA(bt.Strategy):


    params = (('fast',5), ('slow',40))



    def __init__(self):
        self.log("Using SMA strategy")
        self.sma_fast = bt.indicators.MovingAverageSimple(self.data1.close, period = self.p.fast)
        self.sma_slow = bt.indicators.MovingAverageSimple(self.data1.close, period = self.p.slow)
        
        self.signal = bt.indicators.CrossOver(self.sma_fast, self.sma_slow)
        self.signal.plotinfo.plot = False

    def log(self, txt, send_telegram=False, color=None):
        value = datetime.now()
        if len(self) > 0:
            print(self.data0)
            value = self.data0.datetime.datetime()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))

    def next(self):

        if not self.position and self.signal == 1:
            self.order = self.buy()

        if self.getposition().size < 0 and self.signal == 1:
            self.order = self.close()
            self.order = self.buy()

        if not self.position and self.signal == -1:
            self.order = self.sell() 

        if self.getposition().size > 0 and self.signal == -1:
            self.order = self.close()
            self.order = self.sell()


    def stop(self):
        print(f'SMA_fast: {self.p.fast}, SMA_slow: {self.p.slow}, final value: {self.broker.getvalue()}')