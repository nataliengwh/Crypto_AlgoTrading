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
class FullMoney(bt.sizers.PercentSizer):
    params = (
        ('percents', 99),
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
            fromdate=dt.datetime(2021, 1, 1),
            todate=dt.datetime(2022, 6, 30),
            nullvalue=0.0
        )
    cerebro.adddata(data)

    dataSentiment = CustomSentimentData(
            name='Sentiment',
            dataname="data/sentSum.csv",
            timeframe=bt.TimeFrame.Minutes,
            fromdate=dt.datetime(2021, 1, 1),
            todate=dt.datetime(2022, 6, 30)#,
            #nullvalue=0.0
    )
    cerebro.adddata(dataSentiment)

    ############## TRADE SETUP ##############
    broker = cerebro.getbroker()
    broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
    broker.setcash(1000000.0)
    # cerebro.addsizer(FullMoney)
    cerebro.addsizer(bt.sizers.AllInSizer,percents=99)
    
    ############## EVALUATION ANALYZERS ##############
    # SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
    cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
    cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

    ############## IMPLEMENT STRATEGIES ##############
    # cerebro.optstrategy(SentimentTrade, 
    #     which_sentiment=[0,1,2], #0/1/2 for flair/vadar/trasnformer
    #     sent_neg_threshold = 0.2,
    #     sent_pos_threshold = 0.8,
    #     period_ema_fast=20, #10
    #     period_ema_slow=50, #100
    #     period_sma_fast=20, #10
    #     period_sma_slow=50, #100
    # )

    ############## IMPLEMENT STRATEGIES ##############
    #cerebro.addstrategy(BnH)  # basic rsi + SMA returns 6xx% return
    cerebro.addstrategy(SentimentTrade,
        sig=0,
        mode=0,
        which_sentiment=2, #0/1/2 for flair/vadar/trasnformer
        sent_neg_threshold = 0.2,
        sent_pos_threshold = 0.8,
        period_ema_fast=1, #10
        period_ema_slow=50, #100
        period_sma_fast=1, #10
        period_sma_slow=50, #100
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
    #print(result[0])
    print_trade_analysis(result[0].analyzers.ta.get_analysis())

    
    # plot result
    if DEBUG:
        pass
        #cerebro.plot(style = 'candle')

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


result_all=[]
for fs in [100]:
    for ff in [20,25,30]:
        for e in [0]: #sig
            for a in [1]: #model
                for b in [0.25,0.3,0.35]:#neg
                    for c in [0.55,0.6,0.65]:#pos
                        for d in [1]:#mode
                            cerebro = bt.Cerebro(quicknotify=True)
                            ############### DATA FOR SINGLE TS ##############
                            data = CustomDataset(
                                    name=COIN_TARGET,
                                    dataname="data/BTCUSDT.csv",
                                    timeframe=bt.TimeFrame.Minutes,
                                    # buy and hold btc in this period is 540% (7.2k to 46.3k)
                                    fromdate=dt.datetime(2021, 1, 1),
                                    todate=dt.datetime(2022, 6, 30),
                                    #nullvalue=0.0
                                )
                            cerebro.adddata(data)

                            dataSentiment = CustomSentimentData(
                                    name='Sentiment',
                                    dataname="data/sentSum.csv",
                                    timeframe=bt.TimeFrame.Minutes,
                                    fromdate=dt.datetime(2021, 1, 1),
                                    todate=dt.datetime(2022, 6, 30),
                                    #nullvalue=0.0
                            )
                            cerebro.adddata(dataSentiment)

                            ############## TRADE SETUP ##############
                            broker = cerebro.getbroker()
                            broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
                            broker.setcash(1000000.0)
                            # cerebro.addsizer(FullMoney)
                            cerebro.addsizer(bt.sizers.AllInSizer,percents=99)
                            
                            ############## EVALUATION ANALYZERS ##############
                            # SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
                            cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
                            cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
                            cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

                            ############## IMPLEMENT STRATEGIES ##############
                            # cerebro.optstrategy(SentimentTrade, 
                            #     which_sentiment=[0,1,2], #0/1/2 for flair/vadar/trasnformer
                            #     sent_neg_threshold = 0.2,
                            #     sent_pos_threshold = 0.8,
                            #     period_ema_fast=20, #10
                            #     period_ema_slow=50, #100
                            #     period_sma_fast=20, #10
                            #     period_sma_slow=50, #100
                            # )

                            ############## IMPLEMENT STRATEGIES ##############
                            #cerebro.addstrategy(BnH)  # basic rsi + SMA returns 6xx% return
                            cerebro.addstrategy(SentimentTrade,
                                sig=e,
                                mode=d,
                                which_sentiment=a, #0/1/2 for flair/vadar/trasnformer
                                sent_neg_threshold = b,
                                sent_pos_threshold = c,
                                period_ema_fast=ff, #10
                                period_ema_slow=fs, #100
                                period_sma_fast=ff, #10
                                period_sma_slow=fs, #100
                            )


                            # Starting backtrader bot
                            initial_value = cerebro.broker.getvalue()
                            print('Starting Portfolio Value: %.2f' % initial_value)
                            result = cerebro.run()
                            
                            # Print analyzers - results
                            final_value = cerebro.broker.getvalue()


                            result_all.append([cerebro.strats,'Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100),result[0].analyzers.sqn.get_analysis(),result[0].analyzers.mysharpe.get_analysis()])

print('sharpe ratio')
sorted([(i,x[3].get('sharperatio'),x[2].get('trades')) for i,x in enumerate(result_all) if x[2].get('trades')>0 and float(x[1][7:-1])>0],key=lambda x: x[1], reverse=True)
print('sqn')
sorted([(i,x[2].get('sqn'),x[2].get('trades')) for i,x in enumerate(result_all) if x[2].get('trades')>0 and float(x[1][7:-1])>0],key=lambda x: x[1], reverse=True)
print('profit')
sorted([(i,float(x[1][7:-1]),x[2].get('trades')) for i,x in enumerate(result_all) if x[2].get('trades')>0 and float(x[1][7:-1])>0],key=lambda x: x[1], reverse=True)

# threshold sentiment trading
# >>> result_all[166]
# [[[(<class 'strategies.sentiment_trade.SentimentTrade'>, (), {'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.05, 'sent_pos_threshold': 0.9, 'period_ema_fast': 20, 'period_ema_slow': 50, 'period_sma_fast': 20, 'period_sma_slow': 50})]], 'Profit -61.171%', AutoOrderedDict([('sqn', -0.7137325789700488), ('trades', 616)]), OrderedDict([('sharperatio', 
# 0.20823830408202332)])]
# >>> result_all[134]
# [[[(<class 'strategies.sentiment_trade.SentimentTrade'>, (), {'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.001, 'sent_pos_threshold': 0.9, 'period_ema_fast': 20, 'period_ema_slow': 50, 'period_sma_fast': 20, 'period_sma_slow': 50})]], 'Profit -63.206%', AutoOrderedDict([('sqn', -0.752615767760883), ('trades', 616)]), OrderedDict([('sharperatio', 
# 0.160744718975942)])]
# >>> result_all[150]
# [[[(<class 'strategies.sentiment_trade.SentimentTrade'>, (), {'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.01, 'sent_pos_threshold': 0.9, 'period_ema_fast': 20, 'period_ema_slow': 50, 'period_sma_fast': 20, 'period_sma_slow': 50})]], 'Profit -63.206%', AutoOrderedDict([('sqn', -0.752615767760883), ('trades', 616)]), OrderedDict([('sharperatio', 0.160744718975942)])]
# >>> result_all[182]
# [[[(<class 'strategies.sentiment_trade.SentimentTrade'>, (), {'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.1, 'sent_pos_threshold': 0.9, 'period_ema_fast': 20, 'period_ema_slow': 50, 'period_sma_fast': 20, 'period_sma_slow': 50})]], 'Profit -63.757%', AutoOrderedDict([('sqn', -0.9146155452866815), ('trades', 630)]), OrderedDict([('sharperatio', 0.040946423243543056)])]

# MA sentiment
# >>> result_all[318]
# [[[(<class '__main__.SentimentTrade'>, (), {'sig': 1, 'mode': 0, 'which_sentiment': 0, 'sent_neg_threshold': 0.5, 'sent_pos_threshold': 0.5, 'period_ema_fast': 30, 'period_ema_slow': 25, 'period_sma_fast': 30, 'period_sma_slow': 25})]], 'Profit 31.235%', AutoOrderedDict([('sqn', 1.5142510357073762), ('trades', 6)]), OrderedDict([('sharperatio', 0.58177304938
# >>> result_all[391]
# [[[(<class '__main__.SentimentTrade'>, (), {'sig': 1, 'mode': 1, 'which_sentiment': 0, 'sent_neg_threshold': 0.5, 'sent_pos_threshold': 0.5, 'period_ema_fast': 25, 'period_ema_slow': 30, 'period_sma_fast': 25, 'period_sma_slow': 30})]], 'Profit 31.235%', AutoOrderedDict([('sqn', 1.5142510357073762), ('trades', 6)]), OrderedDict([('sharperatio', 0.58177304938
# >>> result_all[330]
# [[[(<class '__main__.SentimentTrade'>, (), {'sig': 1, 'mode': 0, 'which_sentiment': 0, 'sent_neg_threshold': 0.5, 'sent_pos_threshold': 0.5, 'period_ema_fast': 50, 'period_ema_slow': 25, 'period_sma_fast': 50, 'period_sma_slow': 25})]], 'Profit 31.110%', AutoOrderedDict([('sqn', 1.111282643944563), ('trades', 5)]), OrderedDict([('sharperatio', 0.5833319262941292)])]
# >>> result_all[475]
# [[[(<class '__main__.SentimentTrade'>, (), {'sig': 1, 'mode': 1, 'which_sentiment': 0, 'sent_neg_threshold': 0.5, 'sent_pos_threshold': 0.5, 'period_ema_fast': 25, 'period_ema_slow': 50, 'period_sma_fast': 25, 'period_sma_slow': 50})]], 'Profit 31.110%', AutoOrderedDict([('sqn', 1.111282643944563), ('trades', 5)]), OrderedDict([('sharperatio', 0.5833319262941292)])]
# >>> result_all[226]
# [[[(<class '__main__.SentimentTrade'>, (), {'sig': 1, 'mode': 0, 'which_sentiment': 2, 'sent_neg_threshold': 0.5, 'sent_pos_threshold': 0.5, 'period_ema_fast': 25, 'period_ema_slow': 20, 'period_sma_fast': 25, 'period_sma_slow': 20})]], 'Profit -29.603%', AutoOrderedDict([('sqn', 0.846430374111296), ('trades', 5)]), OrderedDict([('sharperatio', 0.0311083177718496)])]

# threshold on MA sent
# >>> result_all[1340]
# [[[{'sig': 0, 'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_sma_fast': 10, 'period_sma_slow': 100})]], 'Profit 19.144%', AutoOrderedDict([('sqn', 0.2994891544649217), ('trades', 97)]), OrderedDict([('sharperatio', 0.38405637068891657)])]
# >>> result_all[406]
# [[[{'sig': 0, 'mode': 0, 'which_sentiment': 1, 'sent_neg_threshold': 0.4, 'sent_pos_threshold': 0.51, 'period_sma_fast': 100, 'period_sma_slow': 100})]], 'Profit 34.055%', AutoOrderedDict([('sqn', 0.7839327976566289), ('trades', 12)]), OrderedDict([('sharperatio', 0.6859098200690001)])]
# >>> result_all[737]
# [[[{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.2, 'sent_pos_threshold': 0.7, 'period_sma_fast': 5, 'period_sma_slow': 100})]], 'Profit 44.024%', AutoOrderedDict([('sqn', 0.3291470705224431), ('trades', 61)]), OrderedDict([('sharperatio', 0.5422589230943837)])]
# >>> result_all[205]
# [[[{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_sma_fast': 25, 'period_sma_slow': 100})]], 'Profit 35.301%', AutoOrderedDict([('sqn', 1.0895739151738106), ('trades', 6)]), OrderedDict([('sharperatio', 15.030772076641012)])]

# 2021
#result_all_2021=result_all.copy()

# 20221H
#result_all_2022=result_all.copy()
cerebro = bt.Cerebro(quicknotify=True)
############### DATA FOR SINGLE TS ##############
data = CustomDataset(
        name=COIN_TARGET,
        dataname="data/BTCUSDT.csv",
        timeframe=bt.TimeFrame.Minutes,
        # buy and hold btc in this period is 540% (7.2k to 46.3k)
        # fromdate=dt.datetime(2021, 1, 1),
        # todate=dt.datetime(2021, 12, 31),
        fromdate=dt.datetime(2022, 1, 1),
        todate=dt.datetime(2022, 6, 30),
        nullvalue=0.0
    )
cerebro.adddata(data)

dataSentiment = CustomSentimentData(
        name='Sentiment',
        dataname="data/sentSum.csv",
        timeframe=bt.TimeFrame.Minutes,
        # fromdate=dt.datetime(2021, 1, 1),
        # todate=dt.datetime(2021, 12, 31),
        fromdate=dt.datetime(2022, 1, 1),
        todate=dt.datetime(2022, 6, 30),
        #nullvalue=0.0
)
cerebro.adddata(dataSentiment)

############## TRADE SETUP ##############
broker = cerebro.getbroker()
broker.setcommission(commission=0.001, name=COIN_TARGET)  # Simulating exchange fee
broker.setcash(1000000.0)
# cerebro.addsizer(FullMoney)
cerebro.addsizer(bt.sizers.AllInSizer,percents=99)

############## EVALUATION ANALYZERS ##############
# SQN = Average( profit / risk ) / StdDev( profit / risk ) * SquareRoot( number of trades )
cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="ta")
cerebro.addanalyzer(bt.analyzers.SQN, _name="sqn")
cerebro.addanalyzer(bt.analyzers.SharpeRatio_A, _name='mysharpe')

############## IMPLEMENT STRATEGIES ##############
# cerebro.optstrategy(SentimentTrade, 
#     which_sentiment=[0,1,2], #0/1/2 for flair/vadar/trasnformer
#     sent_neg_threshold = 0.2,
#     sent_pos_threshold = 0.8,
#     period_ema_fast=20, #10
#     period_ema_slow=50, #100
#     period_sma_fast=20, #10
#     period_sma_slow=50, #100
# )

############## IMPLEMENT STRATEGIES ##############
#cerebro.addstrategy(BnH)  # basic rsi + SMA returns 6xx% return
cerebro.addstrategy(SentimentTrade,
    **{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_sma_fast': 25, 'period_sma_slow': 100, 'period_ema_fast': 25, 'period_ema_slow': 100}
)
# Starting backtrader bot
initial_value = cerebro.broker.getvalue()
print('Starting Portfolio Value: %.2f' % initial_value)
result = cerebro.run()

# Print analyzers - results
final_value = cerebro.broker.getvalue()
[cerebro.strats,'Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100),result[0].analyzers.sqn.get_analysis(),result[0].analyzers.mysharpe.get_analysis()]

# Print analyzers - results
final_value = cerebro.broker.getvalue()
print('Final Portfolio Value: %.2f' % final_value)
print('Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100))
print_sqn(result[0].analyzers.sqn.get_analysis())
print('Sharpe Ratio:', result[0].analyzers.mysharpe.get_analysis())
#print(result[0])
print_trade_analysis(result[0].analyzers.ta.get_analysis())

# only this one positive in both period (simple with look back)
#{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_ema_fast': 25, 'period_ema_slow': 100, 'period_sma_fast': 25, 'period_sma_slow': 100}


import matplotlib.pyplot as plt
plt.scatter([(x[2].get('sqn')) for i,x in enumerate(result_all) if x[2].get('trades')>0 and float(x[1][7:-1])>0],
[(float(x[1][7:-1])) for i,x in enumerate(result_all) if x[2].get('trades')>0 and float(x[1][7:-1])>0])
plt.show()