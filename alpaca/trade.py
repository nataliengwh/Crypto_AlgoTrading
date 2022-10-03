import requests, json
from config import *
from bars import getdata

BASE_URL = "https://paper-api.alpaca.markets"
ACCOUNT_URL = "{}/v2/account".format(BASE_URL)
ORDERS_URL = "{}/v2/orders".format(BASE_URL)
POSITIONS_URL = "{}/v2/positions".format(BASE_URL)
HEADERS = {'APCA-API-KEY-ID': API_KEY, 'APCA-API-SECRET-KEY': SECRET_KEY}

def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return json.loads(r.content)


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

def get_orders():
    r = requests.get(ORDERS_URL, headers=HEADERS)
    return json.loads(r.content)


def close_all_position():
    r = requests.delete(POSITIONS_URL, headers=HEADERS)
    return json.loads(r.content)




enter_std=0.5
exit_std=0.5  # 0.5
stop_loss=-0.01  # -0.015

data0, data1 = getdata('BTC/USD', 'ETH/USD')


mean = (data0['close'] - data1['close']).mean()
std = (data0['close'] - data1['close']).std()


enter_upper = mean + (enter_std * std)
exit_upper = mean + (exit_std * std)
enter_lower = mean - (enter_std * std)
exit_lower = mean - (exit_std * std)

print(data0,data1)
# if spread > self.enter_upper:
#     # indicates that cn0 is overpriced
#     short_coin0()
# elif spread < self.enter_lower:
#     # indicates that cn1 is overpriced
#     long_coin0()


# response = create_order("AAPL", 100, "buy", "market", "gtc")
# response = create_order("MSFT", 1000, "buy", "market", "gtc")

# orders = get_orders()

# print(orders)
