import time
import backtrader as bt
import datetime as dt

from ccxtbt import CCXTStore
from config import BINANCE, ENV, PRODUCTION, COIN_BASE, COIN_QUOTE, DEBUG

from strategies.pairs_trading.pairs_trade import PairsTrade
from utils import print_trade_analysis, print_sqn

COIN_TARGET = "BTC"
DEBUG = True
class CustomDataset(bt.feeds.GenericCSVData):
    params = (
        ('datetime', 1),
        ('open', 2),
        ('high', 3),
        ('low', 4),
        ('close', 5),
        ('volume', 6),
    )


class FullMoney(bt.sizers.PercentSizer):
    params = (
        ('percents', 99),
    )


def main():
    cerebro = bt.Cerebro(quicknotify=True)

    coin0, coin1 = ("ETHUSDT", "ACMUSDT")
    data0 = CustomDataset(
        name=coin0,
        dataname="data/pairs_trading/solusdt_5m.csv",
        timeframe=bt.TimeFrame.Minutes,
        # compression=60,
        # fromdate=dt.datetime(2021, 6, 1, 0, 0),
        # todate=dt.datetime(2021, 11, 30, 0, 0),
        # fromdate=dt.datetime(2021, 12, 1, 0, 0),
        # todate=dt.datetime(2022, 6, 30, 0, 0),
        fromdate=dt.datetime(2022, 7, 1, 0, 0),
        todate=dt.datetime(2022, 10, 31, 0, 0),
    )
    data1 = CustomDataset(
        name=coin1,
        dataname="data/pairs_trading/adausdt_5m.csv",
        # dataname="../data/BTCUSDT.csv",
        timeframe=bt.TimeFrame.Minutes,
        # compression=60,
        # fromdate=dt.datetime(2021, 6, 1, 0, 0),
        # todate=dt.datetime(2021, 11, 30, 0, 0),
        # fromdate=dt.datetime(2021, 12, 1, 0, 0),
        # todate=dt.datetime(2022, 6, 30, 0, 0),
        fromdate=dt.datetime(2022, 7, 1, 0, 0),
        todate=dt.datetime(2022, 10, 31, 0, 0),
    )

    # 2020
    # coin0, coin1 = ("ETHUSDT", "XMRUSDT")
    # data0 = CustomDataset(
    #     name=coin0,
    #     dataname="../data/pairs_trading/ETHUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 12, 31, 0, 0),
    #     todate=dt.datetime(2022, 6, 30, 0, 0),
    # )
    # data1 = CustomDataset(
    #     name=coin1,
    #     dataname="../data/pairs_trading/XMRUSDT2020.csv",
    #     # dataname="../data/BTCUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 12, 31, 0, 0),
    #     todate=dt.datetime(2022, 6, 30, 0, 0),
    # )
    # 2021
    # coin0, coin1 = ("BTCUSDT", "ETHUSDT")
    # data0 = CustomDataset(
    #     name=coin0,
    #     dataname="../data/BTCUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 6, 1, 0, 0),
    #     todate=dt.datetime(2021, 11, 30, 0, 0),
    # )
    # data1 = CustomDataset(
    #     name=coin1,
    #     # dataname="../data/pairs_trading/DOTUSDT2021.csv",
    #     dataname="../data/pairs_trading/ETHUSDT.csv",
    #     timeframe=bt.TimeFrame.Minutes,
    #     fromdate=dt.datetime(2021, 6, 1, 0, 0),
    #     todate=dt.datetime(2021, 11, 30, 0, 0),
    # )
    # 2022 1H
    # coin0, coin1 = ("BTCUSDT","ETHUSDT")
    # data0 = CustomDataset(
    #         name=coin0,
    #         dataname="../data/BTCUSDT.csv",
    #         timeframe=bt.TimeFrame.Minutes,
    #         fromdate=dt.datetime(2021, 6, 1, 0, 0),
    #         todate=dt.datetime(2021, 11, 30, 0, 0),
    #     )
    # data1 = CustomDataset(
    #         name=coin1,
    #         dataname="../data/pairs_trading/ETHUSDT.csv",
    #         timeframe=bt.TimeFrame.Minutes,
    #         fromdate=dt.datetime(2021, 6, 1, 0, 0),
    #         todate=dt.datetime(2021, 11, 30, 0, 0),
    # )
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
    broker.setcommission(commission=0.001, name=COIN_BASE)  # Simulating exchange fee
    broker.setcash(1000000)
    cerebro.addsizer(FullMoney)
    
    ############## EVALUATION ANALYZERS ##############
    # SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

    ############## IMPLEMENT STRATEGIES ##############
    # cerebro.addstrategy(RSI)  # basic rsi + SMA returns 6xx% return
    # cerebro.addstrategy(SMA)
    # cerebro.addstrategy(DualThrust)
    # cerebro.addstrategy(PairsTrading,
    #                     lookback=20,
    #                     enter_threshold_size=2,
    #                     exit_threshold_size=0.5,
    #                     loss_limit=-0.015,
    #                     coin0=coin0,
    #                     coin1=coin1,
    #                     )
    cerebro.addstrategy(PairsTrade,
                        coin0=coin0,
                        coin1=coin1,
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
    print(result[0])
    print_trade_analysis(result[0].analyzers.ta.get_analysis())
    
    # plot result
    if DEBUG:
        cerebro.plot(style = 'candle')

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