import time
import backtrader as bt
import datetime as dt
import pandas as pd
from config import BINANCE, ENV, PRODUCTION, COIN_TARGET, COIN_REFER, DEBUG
from strategies.rsi import RSI
from strategies.SMA import SMA
from strategies.Dual_Thrust import DualThrust
from strategies.pairs_trading import PairsTrading
from strategies.pairs_trade import PairsTrade
from utils import print_trade_analysis, print_sqn

from strategies.sentiment_trade import SentimentTrade

class CustomDataset(bt.feeds.GenericCSVData):
    params = (
        ('datetime', 1),
        ('open', 2),
        ('high', 3),
        ('low', 4),
        ('close', 5),
        ('volume', 6),
    )
class CustomSentimentData(bt.feeds.GenericCSVData):
    lines=(
        'sentiment_flair',
        'sentiment_vadar',
        'sentiment_transformer',
        )
    params = (
        ('datetime', 1),
        ('open', -1),
        ('high', -1),
        ('low', -1),
        ('close', -1),
        ('volume', -1),
        ('sentiment_flair', 9),
        ('sentiment_vadar', 10),
        ('sentiment_transformer', 11),
    )


sent = pd.read_csv('data/redditSentiment_5m_sum1.csv').append(pd.read_csv('data/redditSentiment_5m_sum2.csv'))
sent['open_time'] = pd.to_datetime(sent.close_time).dt.round('1s') + pd.Timedelta(hours=8)
sentSum = sent[['open_time','reddit_cnt_l5m_x',
'reddit_positive_cnt_l5m_flair','reddit_negative_cnt_l5m_flair',
'reddit_positive_cnt_l5m_vadar','reddit_negative_cnt_l5m_vadar',
'reddit_positive_cnt_l5m_transformer','reddit_negative_cnt_l5m_transformer',]]
sentSum['reddit_pos_perc_flair'] = sentSum['reddit_positive_cnt_l5m_flair']/sentSum['reddit_cnt_l5m_x']
sentSum['reddit_pos_perc_vadar'] = sentSum['reddit_positive_cnt_l5m_vadar']/sentSum['reddit_cnt_l5m_x']
sentSum['reddit_pos_perc_transformer'] = sentSum['reddit_positive_cnt_l5m_transformer']/sentSum['reddit_cnt_l5m_x']

# sentSum.to_csv('data/sentSum.csv')

price = pd.read_csv('data/BTCUSDT.csv')
price['open_time'] = pd.to_datetime(price.open_time)
price_f = pd.merge(price,sentSum,how='left', on=['open_time'])


def main():
    cerebro = bt.Cerebro(quicknotify=True)
    ############### DATA FOR SINGLE TS ##############
    data = CustomDataset(
            name=COIN_TARGET,
            dataname="data/BTCUSDT.csv",
            timeframe=bt.TimeFrame.Minutes,
            # buy and hold btc in this period is 540% (7.2k to 46.3k)
            fromdate=dt.datetime(2021, 11, 1),
            todate=dt.datetime(2022, 6, 30),
            nullvalue=0.0
        )
    cerebro.adddata(data)

    dataSentiment = CustomSentimentData(
            name='Sentiment',
            dataname="data/sentSum.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2021, 11, 1),
            todate=dt.datetime(2022, 6, 30)#,
            #nullvalue=0.0
    )
    cerebro.adddata(dataSentiment)

    ############## TRADE SETUP ##############
    class FullMoney(bt.sizers.PercentSizer):
        params = (
            ('percents', 99),
        )
    broker = cerebro.getbroker()
    broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
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
    cerebro.addstrategy(SentimentTrade)
    # cerebro.addstrategy(PairsTrade,
    #                     coin0=coin0,
    #                     coin1=coin1,
    #                     )

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




