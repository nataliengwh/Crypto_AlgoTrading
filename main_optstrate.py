import time
import backtrader as bt
import datetime as dt
import pandas as pd
from config import BINANCE, ENV, PRODUCTION, COIN_TARGET, COIN_REFER, DEBUG
from strategies.rsi import RSI
from strategies.SMA_copy import SMA
from strategies.Dual_Thrust import DualThrust
from strategies.pairs_trading import PairsTrading
from strategies.RVI import RVI_strategy
from strategies.BollingerBands import BollingerBands
from utils import print_trade_analysis, print_sqn

class CustomDataset(bt.feeds.GenericCSVData):
    params = (
        ('datetime', 1),
        ('open', 2),
        ('high', 3),
        ('low', 4),
        ('close', 5),
        ('volume', 6),
    )

def main():
    cerebro = bt.Cerebro(quicknotify=True)
    ############## DATA FOR SINGLE TS ##############
    data = CustomDataset(
            name=COIN_TARGET,
            dataname="data/BTCUSDT.csv",
            timeframe=bt.TimeFrame.Minutes,
            # buy and hold btc in this period is 547.016% (7.2k to 46.3k)
            fromdate=dt.datetime(2020, 1, 1), 
            todate=dt.datetime(2021, 12, 31),
            nullvalue=0.0
        )
    cerebro.adddata(data)
    cerebro.resampledata(data, timeframe = bt.TimeFrame.Days)
    # cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)

    ############## DATA FOR MULTI TS ##############
    # coin0, coin1 = ("BTCUSDT","ETHUSDT")
    # data0 = CustomDataset(
    #         name=coin0,
    #         dataname="data/BTCUSDT.csv",
    #         timeframe=bt.TimeFrame.Minutes,
    #         fromdate=dt.datetime(2020, 1, 1), 
    #         todate=dt.datetime(2021, 12, 31),
    #         nullvalue=0.0
    #     )
    # data1 = CustomDataset(
    #         name=coin1,
    #         dataname="data/ETHUSDT.csv",
    #         timeframe=bt.TimeFrame.Minutes,
    #         fromdate=dt.datetime(2020, 1, 1), 
    #         todate=dt.datetime(2021, 12, 31),
    #         nullvalue=0.0
    #     )
    # cerebro.adddata(data0)
    # cerebro.adddata(data1)
    # cerebro.resampledata(data0, timeframe=bt.TimeFrame.Days, compression=1)
    # cerebro.resampledata(data1, timeframe=bt.TimeFrame.Days, compression=1)

    ############## TRADE SETUP ##############
    class FullMoney(bt.sizers.PercentSizer):
        params = (
            ('percents', 99),
        )
    broker = cerebro.getbroker()
    broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
    broker.setcash(1000000.0)
    broker.set_shortcash(True)
    #cerebro.addsizer(FullMoney)
    cerebro.addsizer(bt.sizers.AllInSizer,percents=99)

    ############## EVALUATION ANALYZERS ##############
    # SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

    ############## IMPLEMENT STRATEGIES ##############
    # cerebro.addstrategy(RSI)  # basic rsi + SMA returns 6xx% return
    # cerebro.addstrategy(SMA)
    cerebro.optstrategy(SMA, 
    fast = 20, slow = [25,30,35,40,45,50,55,60,65,70,75,80,85,90,95,100,150,180,200]
    )
    # cerebro.addstrategy(DualThrust)
    ##cerebro.addstrategy(RVI_strategy)
    # cerebro.addstrategy(PairsTrading,
    #                     lookback=20,
    #                     max_lookback=30,
    #                     enter_threshold_size=2, 
    #                     exit_threshold_size=0.5, 
    #                     loss_limit=-0.015,
    #                     coin0=coin0,
    #                     coin1=coin1,
    #                     )
####################################################
    # Starting backtrader bot
####################################################

    # initial_value = cerebro.broker.getvalue()
    # print('Starting Portfolio Value: %.2f' % initial_value)
    result = cerebro.run()


####################################################
    # Print analyzers - results
####################################################

    # final_value = cerebro.broker.getvalue()
    # print('Final Portfolio Value: %.2f' % final_value)
    # print('Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100))
    # print_sqn(result[0].analyzers.sqn.get_analysis())
    # print('Sharpe Ratio:', result[0].analyzers.mysharpe.get_analysis())
    # print_trade_analysis(result[0].analyzers.ta.get_analysis())
    



    # plot result
    # if DEBUG:
    #     cerebro.plot(style = 'candle')

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("finished.")
        time = dt.datetime.now().strftime("%d-%m-%y %H:%M")
        print("Finished finished at time: ", time)
    except Exception as err:
        print("Finished with error: ", err)
        raise