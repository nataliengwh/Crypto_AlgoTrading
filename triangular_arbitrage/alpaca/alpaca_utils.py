import requests
import alpaca_trade_api as alpaca
import math
from config import ALPACA

HEADERS = {'APCA-API-KEY-ID': ALPACA['key'],
           'APCA-API-SECRET-KEY': ALPACA['secret']}

ALPACA_BASE_URL = 'https://paper-api.alpaca.markets'
DATA_URL = 'https://data.alpaca.markets'
rest_api = alpaca.REST(ALPACA['key'], ALPACA['secret'], ALPACA_BASE_URL)


def round_down_decimal(number, decimal):
    return math.floor(number * pow(10, decimal))/pow(10, decimal)

def get_quote(symbol):
    """ get latest price of symbol """
    try:
        quote = requests.get('{0}/v1beta2/crypto/latest/trades?symbols={1}'
                             .format(DATA_URL, symbol), headers=HEADERS)
        return quote.json()['trades']
    except Exception as e:
        print(f"ERROR when fetching symbol price: {e}")
        return False

def get_all_positions():
    try:
        positions = requests.get(
            '{0}/v2/positions'.format(ALPACA_BASE_URL), headers=HEADERS)
        positions = positions.json()
        return positions
    except Exception as e:
        print(f"ERROR when getting all positions from Alpaca: {e}")
        return False

def get_position(symbol):
    """ get position of symbol
    :param symbol: in form of 'BTCUSD'
    :return: position value
    """
    try:
        position = requests.get(
            '{0}/v2/positions/{1}'.format(ALPACA_BASE_URL, symbol), headers=HEADERS)
        position = float(position.json()['qty'])
        # qty = round_down_decimal(position,2)
        return position
    except Exception as e:
        print(f"ERROR when getting position from Alpaca: {e}")
        return False

def place_order(symbol, qty, side):
    """ place order to Alpaca """
    try:
        order = requests.post(
            '{0}/v2/orders'.format(ALPACA_BASE_URL), headers=HEADERS, json={
                'symbol': symbol,
                'qty': qty,
                'side': side,
                'type': 'market',
                'time_in_force': 'gtc',
            })
        return order
    except Exception as e:
        print(f"ERROR when placing order to Alpaca: {e}")
        return False

def get_account_balance():
    """ place order to Alpaca """
    try:
        balance = requests.get(
            '{0}/v2/account'.format(ALPACA_BASE_URL), headers=HEADERS)
        return round(float(balance.json()['portfolio_value']))
    except Exception as e:
        print(f"ERROR when getting account balance: {e}")
        return False

def liquidate_positions():
    """ liquidate all positions """
    try:
        return requests.delete(
            '{0}/v2/positions'.format(ALPACA_BASE_URL), headers=HEADERS)
    except Exception as e:
        print(f"ERROR when liquidating positions from Alpaca: {e}")
        return False
