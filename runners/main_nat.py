import time
import backtrader as bt
import datetime as dt

from ccxtbt import CCXTStore
from config import BINANCE, ENV, PRODUCTION, COIN_BASE, COIN_QUOTE, DEBUG

from sizer.percent import FullMoney
#from strategies.rsi import RSI
from strategies.SMA import SMA
from strategies.Dual_Thrust import DualThrust
from strategies.pairs_trading import PairsTrading
from strategies.pairs_trade import PairsTrade
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

def main():
    cerebro = bt.Cerebro(quicknotify=True)

    if ENV == PRODUCTION:  # Live trading with Binance
        broker_config = {
            'apiKey': BINANCE.get("key"),
            'secret': BINANCE.get("secret"),
            'nonce': lambda: str(int(time.time() * 1000)),
            'enableRateLimit': True,
        }

        store = CCXTStore(exchange='binance', currency=COIN_QUOTE, config=broker_config, retries=5, debug=DEBUG)

        broker_mapping = {
            'order_types': {
                bt.Order.Market: 'market',
                bt.Order.Limit: 'limit',
                bt.Order.Stop: 'stop-loss',
                bt.Order.StopLimit: 'stop limit'
            },
            'mappings': {
                'closed_order': {
                    'key': 'status',
                    'value': 'closed'
                },
                'canceled_order': {
                    'key': 'status',
                    'value': 'canceled'
                }
            }
        }

        broker = store.getbroker(broker_mapping=broker_mapping)
        cerebro.setbroker(broker)

        hist_start_date = dt.datetime.utcnow() - dt.timedelta(minutes=30000)
        data = store.getdata(
            dataname='%s/%s' % (COIN_BASE, COIN_QUOTE),
            name='%s%s' % (COIN_BASE, COIN_QUOTE),
            timeframe=bt.TimeFrame.Minutes,
            fromdate=hist_start_date,
            compression=30,
            ohlcv_limit=99999
        )

        # Add the feed
        cerebro.adddata(data)

    else:  # Backtesting with CSV file
        data = CustomDataset(
            name=COIN_BASE,
            dataname="dataset/binance_nov_18_mar_19_btc.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2018, 9, 20),
            todate=dt.datetime(2019, 3, 13),
            nullvalue=0.0
        )

        cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=30)

        broker = cerebro.getbroker()
        broker.setcommission(commission=0.001, name=COIN_BASE)  # Simulating exchange fee
        broker.setcash(100000.0)
        cerebro.addsizer(FullMoney)

    ############## DATA FOR SINGLE TS ##############
    # SMA 463%
    # min: RSI + SMA 584%
    # day: RSI + SMA 617%
    # data = CustomDataset(
    #         name=COIN_BASE,
    #         dataname="data/BTCUSDT.csv",
    #         timeframe=bt.TimeFrame.Minutes,
    #         # buy and hold btc in this period is 540% (7.2k to 46.3k)
    #         fromdate=dt.datetime(2021, 11, 1),
    #         todate=dt.datetime(2022, 6, 30),
    #         nullvalue=0.0
    #     )
    # cerebro.adddata(data)
    # cerebro.resampledata(data, timeframe = bt.TimeFrame.Days)
    # cerebro.resampledata(data, timeframe=bt.TimeFrame.Minutes, compression=1)

    ############## DATA FOR MULTI TS ##############
    coin0, coin1 = ("BTCUSDT","ETHUSDT")
    data0 = CustomDataset(
            name=coin0,
            dataname="data/BTCUSDT.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2021, 11, 1, 0, 0),
            todate=dt.datetime(2021, 11, 2, 2, 0),
            nullvalue=0.0
        )
    data1 = CustomDataset(
            name=coin1,
            dataname="data/ETHUSDT.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2021, 11, 1, 0, 0),
            todate=dt.datetime(2021, 11, 2, 2, 0),
            nullvalue=0.0
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
    broker.setcommission(commission=0.001, name=COIN_BASE)  # Simulating exchange fee
    broker.setcash(1000000.0)
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