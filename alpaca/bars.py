from numpy import rot90
import config, requests, json, pandas as pd


def getdata(coin0, coin1):
        
    #minute_bar_url = config.BARS_URL + '/5Min?symbols=BTC/USD&limit=1000'
    # minute_bar_url = config.BARS_URL + '?timeframe=5Min&symbols=BTC/USD,ETH/USD&limit=20'
    minute_bar_url_coin0 = config.BARS_URL + f'?timeframe=5T&symbols={coin0}&limit=1000'
    minute_bar_url_coin1 = config.BARS_URL + f'?timeframe=5T&symbols={coin1}&limit=1000'

    r0 = requests.get(minute_bar_url_coin0, headers=config.HEADERS)
    r1 = requests.get(minute_bar_url_coin1, headers=config.HEADERS)

    data0 = pd.DataFrame(r0.json()['bars'][coin0])[['t','o','h','l','c','v']].rename(columns={'t':'datetime', 'o':'open', 'h':'high', 'l':'low', 'c':'close', 'v':'volume'})
    data1 = pd.DataFrame(r1.json()['bars'][coin1])[['t','o','h','l','c','v']].rename(columns={'t':'datetime', 'o':'open', 'h':'high', 'l':'low', 'c':'close', 'v':'volume'})

    return data0[-20:], data1[-20:]


