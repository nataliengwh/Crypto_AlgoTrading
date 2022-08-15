import backtrader as bt
from datetime import datetime
from termcolor import colored

class BnH(bt.Strategy):

    def __init__(self):
        self.log("Using Buy and Hold strategy")

    def log(self, txt, send_telegram=False, color=None):
        value = datetime.now()
        if len(self) > 0:
            print(self.data0)
            value = self.data0.datetime.datetime()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))
    
    def start(self):
        pass

    def nextstart(self):
        self.buy()

    def next(self):
        pass

    def stop(self):
        self.sell()