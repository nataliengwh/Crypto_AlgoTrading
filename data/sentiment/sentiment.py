import pandas as pd
import datetime as dt

sent = pd.read_csv('data/redditSentiment_5m_sum1.csv').append(pd.read_csv('data/redditSentiment_5m_sum2.csv'))
sent['open_time'] = pd.to_datetime(sent.close_time).dt.round('1s') + pd.Timedelta(hours=8)
sentSum = sent[['open_time','reddit_cnt_l5m_x',
'reddit_positive_cnt_l5m_flair','reddit_negative_cnt_l5m_flair',
'reddit_positive_cnt_l5m_vadar','reddit_negative_cnt_l5m_vadar',
'reddit_positive_cnt_l5m_transformer','reddit_negative_cnt_l5m_transformer',]]
sentSum['reddit_pos_perc_flair'] = sentSum['reddit_positive_cnt_l5m_flair']/sentSum['reddit_cnt_l5m_x']
sentSum['reddit_pos_perc_vadar'] = sentSum['reddit_positive_cnt_l5m_vadar']/sentSum['reddit_cnt_l5m_x']
sentSum['reddit_pos_perc_transformer'] = sentSum['reddit_positive_cnt_l5m_transformer']/sentSum['reddit_cnt_l5m_x']


