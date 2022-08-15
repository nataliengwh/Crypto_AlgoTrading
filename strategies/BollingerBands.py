import backtrader as bt
from datetime import datetime, time
from termcolor import colored

class BollingerBands(bt.Strategy):
    params = (
        ("period", 20),
        ("devfactor", 1),
        ("debug", False)
        )


    def __init__(self):
        self.log("Using Bollinger Bands strategy")
        self.boll = bt.indicators.BollingerBands(self.data1.close, period=self.p.period, devfactor=self.p.devfactor)
        #self.sx = bt.indicators.CrossDown(self.data.close, self.boll.lines.top)
        #self.lx = bt.indicators.CrossUp(self.data.close, self.boll.lines.bot)    
        self.boll = self.boll()

        # self.data1.plotinfo.plot = False
        # self.buy_signal.plotinfo.plot = False
        # self.sell_signal.plotinfo.plot = False


    def log(self, txt, send_telegram=False, color=None):
        value = datetime.now()
        if len(self) > 0:
            print(self.data0)
            value = self.data0.datetime.datetime()

        if color:
            txt = colored(txt, color)

        print('[%s] %s' % (value.strftime("%d-%m-%y %H:%M"), txt))





    def next(self):
 
        if not self.position:
 
            if self.data.close > self.boll.lines.top:
                self.buy()

            if self.data.close < self.boll.lines.bot:
                self.sell()
 
 
        else:
            if self.getposition().size > 0 and self.data.close < self.boll.lines.mid:
                self.close()
                
 
            if self.getposition().size < 0 and self.data.close > self.boll.lines.mid:
                self.close()
                
                