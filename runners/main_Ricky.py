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

from strategies.sentiment_trade_simple_with_look_back import SentimentTrade

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

import multiprocessing as mp
print("Number of processors: ", mp.cpu_count())



t0 = time.time()
result_all_2021_consol=[]
result_all_2022_consol=[]
for fs in [100]:
    for ff in [5,10,25,50,100]: #
        for e in [0]: #sig
            for a in [0,1,2]: #model
                for b in [0.2,0.3,0.4,0.49]:#neg #
                    for c in [0.6,0.7,0.8,0.51]:#pos #
                        for d in [0,1]:#mode
                            
                            cerebro = bt.Cerebro(quicknotify=True)
                            ############### DATA FOR SINGLE TS ##############
                            data = CustomDataset(
                                    name=COIN_TARGET,
                                    dataname="data/BTCUSDT.csv",
                                    timeframe=bt.TimeFrame.Minutes,
                                    # buy and hold btc in this period is 540% (7.2k to 46.3k)
                                    fromdate=dt.datetime(2021, 1, 1),
                                    todate=dt.datetime(2021, 12, 31),
                                    #nullvalue=0.0
                                )
                            cerebro.adddata(data)

                            dataSentiment = CustomSentimentData(
                                    name='Sentiment',
                                    dataname="data/sentSum.csv",
                                    timeframe=bt.TimeFrame.Minutes,
                                    fromdate=dt.datetime(2021, 1, 1),
                                    todate=dt.datetime(2021, 12, 31),
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
                            result = cerebro.run()
                            
                            # Print analyzers - results
                            final_value = cerebro.broker.getvalue()
                            result_all_2021_consol.append([cerebro.strats,'Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100),result[0].analyzers.sqn.get_analysis(),result[0].analyzers.mysharpe.get_analysis()])
                            


                            cerebro = bt.Cerebro(quicknotify=True)
                            ############### DATA FOR SINGLE TS ##############
                            data = CustomDataset(
                                    name=COIN_TARGET,
                                    dataname="data/BTCUSDT.csv",
                                    timeframe=bt.TimeFrame.Minutes,
                                    # buy and hold btc in this period is 540% (7.2k to 46.3k)
                                    fromdate=dt.datetime(2022, 1, 1),
                                    todate=dt.datetime(2022, 6, 30),
                                    #nullvalue=0.0
                                )
                            cerebro.adddata(data)

                            dataSentiment = CustomSentimentData(
                                    name='Sentiment',
                                    dataname="data/sentSum.csv",
                                    timeframe=bt.TimeFrame.Minutes,
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
                            result = cerebro.run()
                            
                            # Print analyzers - results
                            final_value = cerebro.broker.getvalue()

                            result_all_2022_consol.append([cerebro.strats,'Profit %.3f%%' % ((final_value - initial_value) / initial_value * 100),result[0].analyzers.sqn.get_analysis(),result[0].analyzers.mysharpe.get_analysis()])

t1 = time.time()
print(t1-t0)

import pickle
filehandler = open('result_all_2022_consol.pkl', 'wb') 
pickle.dump(result_all_2022_consol, filehandler)
filehandler.close()
filehandler = open('result_all_2021_consol.pkl', 'wb') 
pickle.dump(result_all_2021_consol, filehandler)
filehandler.close()

filehandler = open('result_all_2022_consol.pkl', 'rb') 
result_all_2022_consol = pickle.load(filehandler)
filehandler.close()
filehandler = open('result_all_2021_consol.pkl', 'rb') 
result_all_2021_consol = pickle.load(filehandler)
filehandler.close()


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
# cerebro.addstrategy(SentimentTrade,
#     **{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_sma_fast': 25}
# )

# only this one positive in both period (simple with look back)
#{'sig': 0, 'mode': 1, 'which_sentiment': 1, 'sent_neg_threshold': 0.3, 'sent_pos_threshold': 0.6, 'period_sma_fast': 25}



import matplotlib.pyplot as plt
plt.scatter([(float(x[1][7:-1])) for i,x in enumerate(result_all_2021_consol) if x[0][0][0][2].get('which_sentiment')==0 and x[0][0][0][2].get('mode')==0],
[(float(x[1][7:-1])) for i,x in enumerate(result_all_2022_consol) if x[0][0][0][2].get('which_sentiment')==0 and x[0][0][0][2].get('mode')==0])
plt.show()

import pickle

m = 1
ws = 2
zipped=list(zip([i for i,x in enumerate(result_all_2021_consol) if x[0][0][0][2].get('which_sentiment')==ws and x[0][0][0][2].get('mode')==m],
    [(float(x[1][7:-1])) for i,x in enumerate(result_all_2021_consol) if x[0][0][0][2].get('which_sentiment')==ws and x[0][0][0][2].get('mode')==m],
    [(float(x[1][7:-1])) for i,x in enumerate(result_all_2022_consol) if x[0][0][0][2].get('which_sentiment')==ws and x[0][0][0][2].get('mode')==m]
    ))

# sorted(zipped.copy(),key=lambda x: x[1], reverse=True)[:5]
# sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)[:5]
result_all_2021_consol[167]



0,0
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(2, 30.546, -4.892), (60, 7.818, 1.391), (56, 1.507, 5.662), (68, 0.76, 0.07), (62, 0.711, -0.032), (14, 0.123, -3.753), (4, 0.0, 0.265), (10, 0.0, 0.233), (16, 0.0, -0.139), (58, 0.0, 0.0), (64, 0.0, 0.0), (70, 0.0, 0.0),.163), (6, -29.398, -31.147), (0, -30.727, -34.221), (54, -36.6, 8.519)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(54, -36.6, 8.519), (56, 1.507, 5.662), (60, 7.818, 1.391), (4, 0.0, 0.265), (10, 0.0, 0.233), (68, 0.76, 0.07), (58, 0.0, 0.0), (64, 0.0, 0.0), (70, 0.0, 0.0), (110, 0.0, 0.0), (112, 0.0, 0.0), (116, 0.0, 0.0), (118, 0.0, 0.0), (122, 0.0, 0.0), (124, 0.0, 0.0), (62, 0.711, -0.032), (16, 0.0, -0.139), (120, 0.0, -0.413), (66, -4.728, -2.018), (14, 0.123, -3.753), (8, -3.024, -4.725), (2, 30.546, -4.892), (114, 0.0, -5.453), (108, 0.0, -17.685), (6, -29.398, -31.147), (12, -27.65, -31.163), (0, -30.727, -34.221)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(2, 30.546, -4.892), (56, 1.507, 5.662), (60, 7.818, 1.391), (68, 0.76, 0.07), (62, 0.711, -0.032), (4, 0.0, 0.265), (10, 0.0, 0.233), (58, 0.0, 0.0), (64, 0.0, 0.0), (70, 0.0, 0.0), (110, 0.0, 0.0), (112, 0.0, 0.0), (116, 0.0, 0.0), (118, 0.0, 0.0), (122, 0.0, 0.0), (124, 0.0, 0.0), (16, 0.0, -0.139), (120, 0.0, -0.413), (14, 0.123, -3.753), (66, -4.728, -2.018), (114, 0.0, -5.453), (8, -3.024, -4.725), (54, -36.6, 8.519), (108, 0.0, -17.685), (12, -27.65, -31.163), (6, -29.398, -31.147), (0, -30.727, -34.221)]

0,1
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(18, 73.565, -65.048), (72, 61.065, -56.556), (78, 53.211, -22.921), (126, 31.299, -53.96), (26, 2.757, -23.96), (22, 0.0, -3.658), (28, 0.0, -1.4), (34, 0.0, -1.387), (74, 0.0, -24.59), (76, 0.0, 0.0), (80, 0.0, -2.538), 
(82, 0.0, 0.0), (86, 0.0, -0.755), (88, 0.0, 0.0), (128, 0.0, 0.0), (130, 0.0, 0.0), (134, 0.0, 0.0), (136, 0.0, 0.0), (140, 0.0, 0.0), (142, 0.0, 0.0), (132, -0.365, -56.396), (84, -1.154, -19.535), (138, -1.71, -3.641), (32, -3.407, -19.915), (24, -8.348, -70.569), (20, -24.938, -49.977), (30, -32.555, -76.348)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(76, 0.0, 0.0), (82, 0.0, 0.0), (88, 0.0, 0.0), (128, 0.0, 0.0), (130, 0.0, 0.0), (134, 0.0, 0.0), (136, 0.0, 0.0), (140, 0.0, 0.0), (142, 0.0, 0.0), (86, 0.0, -0.755), (34, 0.0, -1.387), (28, 0.0, -1.4), (80, 0.0, -2.538), (138, -1.71, -3.641), (22, 0.0, -3.658), (84, -1.154, -19.535), (32, -3.407, -19.915), (78, 53.211, -22.921), (26, 2.757, -23.96), (74, 0.0, -24.59), (20, -24.938, -49.977), (126, 31.299, -53.96), (132, -0.365, -56.396), (72, 61.065, -56.556), (18, 73.565, -65.048), (24, -8.348, -70.569), (30, -32.555, -76.348)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(78, 53.211, -22.921), (76, 0.0, 0.0), (82, 0.0, 0.0), (88, 0.0, 0.0), (128, 0.0, 0.0), (130, 0.0, 0.0), (134, 0.0, 0.0), (136, 0.0, 0.0), (140, 0.0, 0.0), (142, 0.0, 0.0), (86, 0.0, -0.755), (34, 0.0, -1.387), (28, 0.0, -1.4), (80, 0.0, -2.538), (22, 0.0, -3.658), (138, -1.71, -3.641), (84, -1.154, -19.535), (32, -3.407, -19.915), (26, 2.757, -23.96), (74, 0.0, -24.59), (72, 61.065, -56.556), (18, 73.565, -65.048), (126, 31.299, -53.96), (132, -0.365, -56.396), (20, -24.938, -49.977), (24, -8.348, -70.569), (30, -32.555, -76.348)]

0,2
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(90, 0.549, 0.0), (44, 0.507, -0.746), (46, 0.507, -0.026), (50, 0.507, -0.511), (52, 0.507, -0.026), (102, 0.462, 0.0), (96, 0.413, 0.0), (38, 0.261, -0.402), (40, 0.261, -0.366), (92, 0.0, 0.0), (94, 0.0, 0.0), (98, 0.0, 0.0), (100, 0.0, 0.0), (104, 0.0, 0.0), (106, 0.0, 0.0), (144, 0.0, 0.0), (146, 0.0, 0.0), (148, 0.0, 0.0), (150, 0.0, 0.0), (152, 0.0, 0.0), (154, 0.0, 0.0), (156, 0.0, 0.0), (158, 0.0, 0.0), (160, 0.0, 0.0), (48, -0.109, -6.506), (42, -0.695, -7.025), (36, -4.449, -7.124)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(90, 0.549, 0.0), (92, 0.0, 0.0), (94, 0.0, 0.0), (96, 0.413, 0.0), (98, 0.0, 0.0), (100, 0.0, 0.0), (102, 0.462, 0.0), (104, 0.0, 0.0), (106, 0.0, 0.0), (144, 0.0, 0.0), (146, 0.0, 0.0), (148, 0.0, 0.0), (150, 0.0, 0.0), (152, 0.0, 0.0), (154, 0.0, 0.0), (156, 0.0, 0.0), (158, 0.0, 0.0), (160, 0.0, 0.0), (46, 0.507, -0.026), (52, 0.507, -0.026), (40, 0.261, -0.366), (38, 0.261, -0.402), (50, 0.507, -0.511), (44, 0.507, -0.746), (48, -0.109, -6.506), (42, -0.695, -7.025), (36, -4.449, -7.124)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(90, 0.549, 0.0), (102, 0.462, 0.0), (46, 0.507, -0.026), (52, 0.507, -0.026), (96, 0.413, 0.0), (92, 0.0, 0.0), (94, 0.0, 0.0), (98, 0.0, 0.0), (100, 0.0, 0.0), (104, 0.0, 0.0), (106, 0.0, 0.0), (144, 0.0, 0.0), (146, 0.0, 0.0), (148, 0.0, 0.0), (150, 0.0, 0.0), (152, 0.0, 0.0), (154, 0.0, 0.0), (156, 0.0, 0.0), (158, 0.0, 0.0), (160, 0.0, 0.0), (40, 0.261, -0.366), (50, 0.507, -0.511), (38, 0.261, -0.402), (44, 0.507, -0.746), (48, -0.109, -6.506), (42, -0.695, -7.025), (36, -4.449, -7.124)]

1,0
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(55, 152.714, -57.988), (1, 106.536, -61.783), (9, 65.339, -59.056), (115, 61.561, -54.27), (117, 61.561, -54.27), (119, 61.561, -54.27), (11, 60.727, -56.921), (5, 60.716, -52.018), (121, 60.511, -56.56), (123, 60.511, -56.56), (125, 60.511, -56.56), (63, 60.483, -56.709), (65, 60.483, -56.495), (69, 60.404, -56.903), (71, 60.404, -56.646), (17, 60.333, -56.823), (67, 59.804, -59.888), (15, 59.496, -59.525), (57, 59.219, -54.468), (59, 59.219, -51.716), (61, 45.719, -61.102), (7, 41.419, -72.334), (3, 22.784, -54.123), (13, 14.56, -74.839), (109, 0.0, -47.534), (111, 0.0, -47.534), (113, 0.0, -47.534)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(109, 0.0, -47.534), (111, 0.0, -47.534), (113, 0.0, -47.534), (59, 59.219, -51.716), (5, 60.716, -52.018), (3, 22.784, -54.123), (115, 61.561, -54.27), (117, 61.561, -54.27), (119, 61.561, -54.27), (57, 59.219, -54.468), (65, 60.483, -56.495), (121, 60.511, -56.56), (123, 60.511, -56.56), (125, 60.511, -56.56), (71, 60.404, -56.646), (63, 60.483, -56.709), (17, 60.333, -56.823), (69, 60.404, -56.903), (11, 60.727, -56.921), (55, 152.714, -57.988), (9, 65.339, -59.056), (15, 59.496, -59.525), (67, 59.804, -59.888), (61, 45.719, -61.102), (1, 106.536, -61.783), (7, 41.419, -72.334), (13, 14.56, -74.839)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(55, 152.714, -57.988), (1, 106.536, -61.783), (5, 60.716, -52.018), (59, 59.219, -51.716), (115, 61.561, -54.27), (117, 61.561, -54.27), (119, 61.561, -54.27), (57, 59.219, -54.468), (65, 60.483, -56.495), (121, 60.511, -56.56), (123, 60.511, -56.56), (125, 60.511, -56.56), (9, 65.339, -59.056), (71, 60.404, -56.646), (63, 60.483, -56.709), (11, 60.727, -56.921), (17, 60.333, -56.823), (69, 60.404, -56.903), (15, 59.496, -59.525), (67, 59.804, -59.888), (61, 45.719, -61.102), (3, 22.784, -54.123), (109, 0.0, -47.534), (111, 0.0, -47.534), (113, 0.0, -47.534), (7, 41.419, -72.334), (13, 14.56, -74.839)]

1,1
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(21, 107.996, -30.756), (139, 62.499, -56.352), (141, 61.577, -56.801), (143, 61.577, -56.801), (23, 60.727, -56.889), (29, 60.685, -58.446), (81, 60.48, -56.399), (83, 60.48, -56.366), (87, 60.404, -57.695), (89, 60.404, -56.884), (35, 60.333, -58.329), (33, 55.244, -66.274), (27, 47.425, -62.712), (85, 38.787, -68.488), (75, 35.751, -38.892), (77, 35.751, -53.627), (135, 15.527, -47.968), (137, 15.527, -47.968), (133, 15.304, 17.343), (127, 0.0, 0.0), (129, 0.0, 0.0), (131, 0.0, 0.0), (25, -0.795, -68.05), (73, -1.132, -1.499), (79, -3.425, -58.444), (19, -11.008, -17.225), (31, -23.358, -83.703)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(133, 15.304, 17.343), (127, 0.0, 0.0), (129, 0.0, 0.0), (131, 0.0, 0.0), (73, -1.132, -1.499), (19, -11.008, -17.225), (21, 107.996, -30.756), (75, 35.751, -38.892), (135, 15.527, -47.968), (137, 15.527, -47.968), (77, 35.751, -53.627), (139, 62.499, -56.352), (83, 60.48, -56.366), (81, 60.48, -56.399), (141, 61.577, -56.801), (143, 61.577, -56.801), (89, 60.404, -56.884), (23, 60.727, -56.889), (87, 60.404, -57.695), (35, 60.333, -58.329), (79, -3.425, -58.444), (29, 60.685, -58.446), (27, 47.425, -62.712), (33, 55.244, -66.274), (25, -0.795, -68.05), (85, 38.787, -68.488), (31, -23.358, -83.703)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(133, 15.304, 17.343), (21, 107.996, -30.756), (127, 0.0, 0.0), (129, 0.0, 0.0), (131, 0.0, 0.0), (73, -1.132, -1.499), (75, 35.751, -38.892), (19, -11.008, -17.225), (139, 62.499, -56.352), (141, 61.577, -56.801), (143, 61.577, -56.801), (83, 60.48, -56.366), (81, 60.48, -56.399), (23, 60.727, -56.889), (89, 60.404, -56.884), (87, 60.404, -57.695), (29, 60.685, -58.446), (35, 60.333, -58.329), (77, 35.751, -53.627), (33, 55.244, -66.274), (27, 47.425, -62.712), (135, 15.527, -47.968), (137, 15.527, -47.968), (85, 38.787, -68.488), (79, -3.425, -58.444), (25, -0.795, -68.05), (31, -23.358, -83.703)]

1,2
>>> sorted(zipped.copy(),key=lambda x: x[1], reverse=True)
[(37, 66.023, -60.765), (39, 60.727, -57.068), (41, 60.727, -56.726), (157, 60.511, -56.715), (159, 60.511, -56.715), (161, 60.511, -56.715), (97, 60.483, -56.715), (99, 60.483, -56.715), (101, 60.483, -56.715), (103, 60.404, -56.734), (105, 60.404, -56.734), (107, 60.404, -56.734), (45, 60.333, -56.921), (47, 60.333, -56.871), (151, 60.323, -57.108), (153, 60.323, -57.108), (155, 60.323, -57.108), (91, 60.265, -57.038), (93, 60.265, -57.038), (95, 60.265, -57.038), (51, 60.042, -57.056), (53, 60.042, -56.905), (43, 59.09, -61.115), (49, 57.406, -61.36), (145, 51.975, -52.414), (147, 51.975, -52.414), (149, 51.975, -52.414)]
>>> sorted(zipped.copy(),key=lambda x: x[2], reverse=True)
[(145, 51.975, -52.414), (147, 51.975, -52.414), (149, 51.975, -52.414), (97, 60.483, -56.715), (99, 60.483, -56.715), (101, 60.483, -56.715), (157, 60.511, -56.715), (159, 60.511, -56.715), (161, 60.511, -56.715), (41, 60.727, -56.726), (103, 60.404, -56.734), (105, 60.404, -56.734), (107, 60.404, -56.734), (47, 60.333, -56.871), (53, 60.042, -56.905), (45, 60.333, -56.921), (91, 60.265, -57.038), (93, 60.265, -57.038), (95, 60.265, -57.038), (51, 60.042, -57.056), (39, 60.727, -57.068), (151, 60.323, -57.108), (153, 60.323, -57.108), (155, 60.323, -57.108), (37, 66.023, -60.765), (43, 59.09, -61.115), (49, 57.406, -61.36)]
>>> sorted(zipped.copy(),key=lambda x: x[2]*2+x[1], reverse=True)
[(41, 60.727, -56.726), (145, 51.975, -52.414), (147, 51.975, -52.414), (149, 51.975, -52.414), (157, 60.511, -56.715), (159, 60.511, -56.715), (161, 60.511, -56.715), (97, 60.483, -56.715), (99, 60.483, -56.715), (101, 60.483, -56.715), (103, 60.404, -56.734), (105, 60.404, -56.734), (107, 60.404, -56.734), (39, 60.727, -57.068), (47, 60.333, -56.871), (45, 60.333, -56.921), (53, 60.042, -56.905), (91, 60.265, -57.038), (93, 60.265, -57.038), (95, 60.265, -57.038), (151, 60.323, -57.108), (153, 60.323, -57.108), (155, 60.323, -57.108), (51, 60.042, -57.056), (37, 66.023, -60.765), (43, 59.09, -61.115), (49, 57.406, -61.36)]