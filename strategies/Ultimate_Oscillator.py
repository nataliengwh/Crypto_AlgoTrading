import backtrader as bt
from datetime import datetime, time
from termcolor import colored

# class DT_line(bt.Indicator):
#     lines = ('U','D')
#     params = (('period',2), ('k_u',0.7), ('k_d', 0.7))

#     def __init__(self) -> None:
#         self.addminperiod(self.p.period + 1)
    
#     def next(self):
#         HH = max(self.data.high.get(-1, size = self.p.period))
#         LC = min(self.data.close.get(-1, size = self.p.period))
#         HC = max(self.data.close.get(-1, size = self.p.period))
#         LL = min(self.data.low.get(-1, size = self.p.period))
#         R = max(HH - LC, HC - LL)
#         self.lines.U[0] = self.data.open[0] + self.p.k_u * R
#         self.lines.D[0] = self.data.open[0] - self.p.k_d * R



class UltimateOscillator(bt.Strategy):
    params = (('period_1',7), ('period_2',14), ('period_3', 28))
    
    def __init__(self):
        self.log("Using Ultimate Oscillator strategy")
        self.dataclose = self.data0.close
        self.ULTOSC = bt.talib.ULTOSC(self.data1.high, self.data1.low, self.data1.close, timeperiod1 = self.p.period_1,
                                                                                        timeperiod2 = self.p.period_2, 
                                                                                        timeperiod3 = self.p.period_3)

        #self.D_line.plotinfo.plotmaster = self.data0

        #self.buy_signal = bt.indicators.CrossOver(self.dataclose, self.D_line.U)
        #self.sell_signal = bt.indicators.CrossDown(self.dataclose, self.D_line.D)

        self.data1.plotinfo.plot = False
        #self.buy_signal.plotinfo.plot = False
        #self.sell_signal.plotinfo.plot = False


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
        # if not self.position and self.ULTOSC < 30 :
        #     self.order = self.buy()
        # if not self.position and self.ULTOSC > 70:
        #     self.order = self.sell()
        
        # if self.getposition().size < 0 and self.ULTOSC < 30:
        #     self.order = self.close()
        #     self.order = self.buy()
        # if self.getposition().size > 0 and self.ULTOSC > 70:
        #     self.order = self.close()
        #     self.order = self.sell()



        if not self.position and self.ULTOSC < 30:
            self.order = self.sell()
        if not self.position and self.ULTOSC > 70:
            self.order = self.buy()
        
        if self.getposition().size < 0 and self.ULTOSC < 30:
            self.order = self.close()
            self.order = self.sell()
        if self.getposition().size > 0 and self.ULTOSC > 70:
            self.order = self.close()
            self.order = self.buy()
    # def stop(self):
    #     print('period: %s, k_u: %s, k_d: %s, final value: %.2f' %(
    #         self.p.period, self.p.k_u, self.p.k_d, self.broker.getvalue()
    #     ))