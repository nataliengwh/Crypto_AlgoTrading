from turtle import pos
import backtrader as bt
from datetime import datetime, time
from termcolor import colored
import numpy as np
import math



class RVI(bt.Indicator):
    params = (('period', 10),)
    lines = ('std','pos','neg','rvi')
    plotinfo = dict(subplot = False)
    plotlines = dict(
        std = dict(_plotskip = True),
        pos = dict(_plotskip = True),
        neg = dict(_plotskip = True),
        rvi = dict(_plotskip = False)
    )

    def __init__(self) -> None:
        self.lines.std = bt.talib.STDDEV(self.data.close, timeperiod = 10, nbdev = 2.0)


    def next(self):
        if self.lines.std[0] > self.lines.std[-1]:
            self.lines.pos[0] = self.lines.std[0]
        
        else:
            self.lines.pos[0] = 0
        
        if self.lines.std[0] < self.lines.std[-1]:
            self.lines.neg[0] = self.lines.std[0]
        else:
            self.lines.neg[0] = 0
        
        pos_nan = np.nan_to_num(self.lines.pos.get(size = self.params.period))
        neg_nan = np.nan_to_num(self.lines.neg.get(size = self.params.period))

        Usum = math.fsum(pos_nan)
        Dsum = math.fsum(neg_nan)

        if (Usum + Dsum) == 0:
            self.lines.rvi[0] = 0
            return
        self.lines.rvi[0] = 100* Usum/(Usum+Dsum)

class RVI_strategy(bt.Strategy):
    #params = (('period',2), ('k_u',0.7), ('k_d', 0.7))
    
    def __init__(self):
        self.log("Using RVI strategy")
        self.rvi = RVI()
        self.close = self.data.close

        # self.buy_signal = bt.indicators.CrossOver(self.dataclose, self.D_line.U)
        # self.sell_signal = bt.indicators.CrossDown(self.dataclose, self.D_line.D)

        self.data1.plotinfo.plot = False
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
        # if self.data.datetime.time() > time(0, 15) and self.data.datetime.time() < time(23, 45):
        up = 60
        down = 35
        
        if not self.positions:
            if self.rvi.rvi[0] > up:
                if self.rvi.rvi[-1] < up and self.rvi.rvi[-2] < up:
                    self.order = self.buy()
        
        else:
            if self.rvi.rvi[0] < down:
                if self.rvi.rvi[-1] > down and self.rvi.rvi[-2] > down:
                    self.order = self.sell()


        # if self.data.datetime.time() >= time(23, 45) and self.position:
        #     self.order = self.close()

    # def stop(self):
    #     print('period: %s, k_u: %s, k_d: %s, final value: %.2f' %(
    #         self.p.period, self.p.k_u, self.p.k_d, self.broker.getvalue()
    #     ))