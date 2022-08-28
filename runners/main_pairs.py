import backtrader as bt
import datetime as dt
import pandas as pd
from config import BINANCE, ENV, PRODUCTION, COIN_TARGET, COIN_REFER, DEBUG
from strategies.pairs_trading import PairsTrading
from strategies.pairs_trade import PairsTrade
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
    cerebro = bt.Cerebro()
    # 2020
    # coin0, coin1 = ("ETHUSDT", "XMRUSDT")
    # data0 = CustomDataset(
    #     name=coin0,
    #     dataname="data/ETHUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2020, 1, 1, 0, 0),
    #     todate=dt.datetime(2020, 12, 31, 0, 0),
    # )
    # data1 = CustomDataset(
    #     name=coin1,
    #     dataname="data/pair_trade/XMRUSDT2020.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2020, 1, 1, 0, 0),
    #     todate=dt.datetime(2020, 12, 31, 0, 0),
    # )
    # 2021
    # coin0, coin1 = ("BTCUSDT", "DOTUSDT")
    # data0 = CustomDataset(
    #     name=coin0,
    #     dataname="data/BTCUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 1, 1, 0, 0),
    #     todate=dt.datetime(2021, 12, 31, 0, 0),
    # )
    # data1 = CustomDataset(
    #     name=coin1,
    #     dataname="data/pair_trade/DOTUSDT2021.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 1, 1, 0, 0),
    #     todate=dt.datetime(2021, 12, 31, 0, 0),
    # )
    # 2022 1H
    coin0, coin1 = ("BTCUSDT","BCHUSDT")
    data0 = CustomDataset(
            name=coin0,
            dataname="data/BTCUSDT.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2022, 1, 1, 0, 0),
            todate=dt.datetime(2022, 6, 30, 0, 0),
        )
    data1 = CustomDataset(
            name=coin1,
            dataname="data/pair_trade/BCHUSDT2022.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2022, 1, 1, 0, 0),
            todate=dt.datetime(2022, 6, 30, 0, 0),
    )
    cerebro.adddata(data0)
    cerebro.adddata(data1)
    # cerebro.resampledata(data0, timeframe=bt.TimeFrame.Days, compression=1)
    # cerebro.resampledata(data1, timeframe=bt.TimeFrame.Days, compression=1)

    ############## TRADE SETUP ##############
    class FullMoney(bt.sizers.PercentSizer):
        params = (
            ('percents', 99),
        )
    broker = cerebro.getbroker()
    broker.setcommission(commission=0.05, name="BTC")  # Simulating exchange fee
    broker.setcash(1000000.0)
    # cerebro.addsizer(FullMoney)
    cerebro.addsizer(bt.sizers.AllInSizer, percents=99)

    ############## EVALUATION ANALYZERS ##############
    # SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

    ############## IMPLEMENT STRATEGIES ##############
    # cerebro.addstrategy(PairsTrading,
    #                     lookback=20,
    #                     enter_threshold_size=2,
    #                     exit_threshold_size=0.5,
    #                     loss_limit=-0.015,
    #                     coin0=coin0,
    #                     coin1=coin1,
    #                     )
    # cerebro.addstrategy(PairsTrade,
    #                     coin0=coin0,
    #                     coin1=coin1,
    #                     )
    cerebro.optstrategy(PairsTrade,
                        lookback=20,
                        enter_std=2,
                        exit_std=[0.5,1],
                        stop_loss=-0.01,
                        )

    # Starting backtrader bot
    initial_value = cerebro.broker.getvalue()
    print('Starting Portfolio Value: %.2f' % initial_value)
    result = cerebro.run()
    
    # Print analyzers - results
    final_value = cerebro.broker.getvalue()
    print('Final Portfolio Value: %.2f' % final_value)
    print('Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100))
    print_sqn(result[0].analyzers.sqn.get_analysis())
    print('Sharpe Ratio:', result[0].analyzers.mysharpe.get_analysis())
    print_trade_analysis(result[0].analyzers.ta.get_analysis())

    # for plotting
    # data1.plotinfo.plotmaster = data0
    # data1.plotinfo.sameaxis = True
    # cerebro.plot()  #style = 'candle')

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