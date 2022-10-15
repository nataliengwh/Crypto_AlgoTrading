import requests, json, schedule, time
from config import *
from bars import getdata
from datetime import datetime

BASE_URL = "https://paper-api.alpaca.markets"
ACCOUNT_URL = "{}/v2/account".format(BASE_URL)
ORDERS_URL = "{}/v2/orders".format(BASE_URL)
POSITIONS_URL = "{}/v2/positions".format(BASE_URL)
QUOTE_URL = "{}/v1beta2/crypto/latest/trades".format(BASE_URL)
HEADERS = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}

enter_std=0.5
exit_std=0.5  # 0.5
stop_loss=0.95  # 0.9
long_BCH = False
long_BTC = False

def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return json.loads(r.content)

def get_cash():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return float(json.loads(r.content)['non_marginable_buying_power'])

def get_portfolio():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return float(json.loads(r.content)['portfolio_value'])

def create_order(symbol, qty, side, type, time_in_force):
    data = {
        "symbol": symbol,
        "qty": qty,
        "side": side,
        "type": type,
        "time_in_force": time_in_force
    }

    r = requests.post(ORDERS_URL, json=data, headers=HEADERS)

    return json.loads(r.content)

def get_position():
    r = requests.get(POSITIONS_URL, headers=HEADERS)
    return json.loads(r.content)


def get_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)
    return json.loads(r.content)


def close_all_position():
    r = requests.delete(POSITIONS_URL, headers=HEADERS)
    return json.loads(r.content)

def get_quote(symbol):

    r = requests.get(f"https://data.alpaca.markets/v1beta2/crypto/latest/quotes?symbols={symbol}", headers=HEADERS)

    return json.loads(r.content)['quotes'][symbol]['ap']

def trade():
    ### Collect data and calculate signal
    data0, data1 = getdata('BTC/USD', 'BCH/USD')
    mean = (data0['close'] - data1['close']).mean()
    std = (data0['close'] - data1['close']).std()
    enter_upper = mean + (enter_std * std)
    exit_upper = mean + (exit_std * std)
    enter_lower = mean - (enter_std * std)
    exit_lower = mean - (exit_std * std)
    spread = float(data0[-1:]['close']) - float(data1[-1:]['close'])
    print(f'Current time : {datetime.now()}\nSpread : {spread}\nUpper and lower : {enter_upper, enter_lower}')
    if get_position() == []:
        if spread > enter_upper:
            create_order('BCH/USD', side = 'buy', qty = get_cash()/get_quote('BCH/USD')-1, type = 'market', time_in_force = 'gtc')
            int_portfolio = get_portfolio()
            long_BCH = True
        elif spread < enter_lower:
            create_order('BTC/USD', side = 'buy', qty = get_cash()/get_quote('BTC/USD')-0.1,type = 'market', time_in_force = 'gtc')
            int_portfolio = get_portfolio()
            long_BTC = True
        print(get_position(), get_portfolio)
    ###check exist###
    if get_position() != []:
        if get_portfolio()/int_portfolio <= stop_loss:
            close_all_position()
            long_BTC = False
            long_BCH = False
        if long_BCH and spread < exit_upper:
            close_all_position()
            long_BCH = False
        if long_BTC and spread > exit_lower:
            close_all_position()
            long_BTC = False

schedule.every(5).minutes.do(trade)
  
while True:
    schedule.run_pending()
    time.sleep(1)
