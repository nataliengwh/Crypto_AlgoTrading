from exchange_api.alpaca_utils import *

# https://alpaca.markets/learn/triangular-arbitrage-with-coin-pair-trading/


waitTime = 3  # seconds between each quote request
investment = 50000
min_profit_pct = 0.3
coins = ['AVAX', 'BCH', 'DOGE', 'ETH', 'LINK', 'LTC', 'MATIC',
         'SOL', 'SUSHI', 'UNI', 'YFI']


def _init_coin_pair_dict(coins: list):
    # create list with symbol based in btc & usd
    full_list = []
    for coin in coins:
        full_list.append(coin+'/BTC')
        full_list.append(coin + '/USD')
    full_list = ",".join(full_list)
    full_list += ",BTC/USD"
    # initiate dictionary for prices
    prices_dict = dict.fromkeys(coins, (0, 0)) # tuple to store (BTC/ USD)
    return prices_dict, full_list

def get_latest_quote(coins) -> dict:
    """
    :param coins: list of coins that have btc denominated pair
    :return: {'COIN': (COIN-BTC px, COIN-USD px)}
    """
    prices_dict, full_list = _init_coin_pair_dict(coins)
    quote_dict = get_quote(full_list)
    # fill prices_dict with quote prices
    for coin in coins:
        to_btc = quote_dict[f"{coin}/BTC"]['p']
        to_usd = quote_dict[f"{coin}/USD"]['p']
        prices_dict[coin] = (to_btc, to_usd)
    prices_dict['BTC/USD'] = quote_dict[f"BTC/USD"]['p']
    return prices_dict

def check_arbitrage_opp(coin, prices_tuple, btc_usd):
    """
    :param prices_tuple: (COIN-BTC px, COIN-USD px)
    :param btc_usd: latest price of BTC/USD
    :return:
    """
    global investment
    global min_profit_pct
    coin_btc, coin_usd = prices_tuple
    threshold = coin_usd / btc_usd
    spread = abs(threshold - coin_btc)
    # BTC/USD is cheaper: buy BTC, convert to COIN, sell COIN
    if threshold > coin_btc * (1 + min_profit_pct/100):
        print("Trade Triggered: BUY/BUY/SELL")
        print(f"Spread: {spread * 100:.5f}")
        buy_btc_qty = investment / btc_usd
        order_1 = place_order("BTC/USD", buy_btc_qty, "buy")
        if order_1.status_code==200:
            print(f"BUY BTC/USD:{buy_btc_qty:,.2} @ {btc_usd:,}")
            print(get_account_balance())
            print(get_all_positions())
            latest_coin_btc = get_quote(f"{coin}/BTC")[f"{coin}/BTC"]['p']
            sell_qty = get_position("BTCUSD") / (latest_coin_btc/0.95)  #(coin_btc/0.95)
            sell_qty = round_down_decimal(sell_qty, 2)
            order_2 = place_order(f"{coin}/BTC", sell_qty, "buy")
            if order_2.status_code==200:
                print(f"Buy {coin}/BTC:{sell_qty:,.2} @ {coin_btc:,.6f}")
                print(get_account_balance())
                print(get_all_positions())
                sell_qty_3 = get_position("BTCUSD")
                order_3 = place_order(f"{coin}/USD", sell_qty_3, "sell")
                if order_3.status_code==200:
                    print(f"Sell {coin}/USD:{sell_qty:,.2} @ {float(coin_usd):,.2}")
                    print(get_account_balance())
                    print(get_all_positions())
                    print("--------------------------------")
                else:
                    place_order(f"{coin}/BTC", sell_qty, "sell")
                    print(f"ERROR when selling {coin}/USD (3rd Trade)")
                    print("--------------------------------")
            else:
                print(f"ERROR when buying {coin}/BTC (2nd Trade)")
                print("--------------------------------")
        else:
            print("ERROR when buying BTC/USD (1st Trade)")
            print("--------------------------------")
        # liquidate_positions()
    # COIN/USD is cheaper: buy COIN, convert to BTC, sell BTC
    elif threshold < coin_btc * (1 - min_profit_pct/100):
        print("Trade Triggered: BUY/SELL/SELL")
        print(f"Spread: {spread * 100:.5f}")
        buy_coin_qty = investment / coin_usd
        order_1 = place_order(f"{coin}/USD", buy_coin_qty, "buy")
        if order_1.status_code==200:
            print(f"Buy {coin}/USD:{buy_coin_qty:,.2f} @ {float(coin_usd):,.2f}")
            print(get_account_balance())
            print(get_all_positions())
            sell_qty_2 = get_position(f"{coin}USD")
            order_2 = place_order(f"{coin}/BTC", sell_qty_2, "sell")
            if order_2.status_code==200:
                print(f"Sell {coin}/BTC:{sell_qty_2:,.2f} @ {coin_btc:,.6f}")
                print(get_account_balance())
                print(get_all_positions())
                sell_qty_3 = get_position("BTCUSD")
                order_3 = place_order(f"BTC/USD", sell_qty_3, "sell")
                if order_3.status_code == 200:
                    print(f"Sell BTC/USD:{sell_qty_3:,.2f} @ {btc_usd:,}")
                    print(get_account_balance())
                    print(get_all_positions())
                    print("--------------------------------")
                else:
                    # _place_order(f"{coin}/BTC", sell_qty, "buy")
                    print("ERROR when selling BTC/USD (3rd Trade)")
                    print("--------------------------------")
            else:
                print(f"ERROR when selling {coin}/BTC (2nd Trade)")
                print("--------------------------------")
        else:
            print(F"ERROR when buying {coin}/USD (1st Trade)")
            print("--------------------------------")
        # liquidate_positions()
    else:
        print(f"No arbitrage opportunity, spread: {spread:.5f}")
        print("--------------------------------")

def main():
    initial_balance = get_account_balance()
    print(initial_balance)
    prices_dict = get_latest_quote(coins)
    btc_usd = prices_dict['BTC/USD']
    for coin, prices_tuple in list(prices_dict.items())[:-1]:
        check_arbitrage_opp(coin, prices_tuple, btc_usd)
    print(f"Position change: {(get_account_balance() - initial_balance):2f}")


if __name__ == "__main__":
    main()