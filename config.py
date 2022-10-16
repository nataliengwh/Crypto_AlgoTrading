import os

PRODUCTION = "production"
DEVELOPMENT = "development"

COIN_BASE = "BTC"
COIN_QUOTE = "USDT"

ENV = os.getenv("ENVIRONMENT", PRODUCTION)
DEBUG = True

BINANCE = {
  "key": "U3w1HkCHfEZpzdgEOBdhZDy5pOZmndmwwuJRPQMmimnbMHp69jaWo890wn3EkEv7",
  "secret": "Di4D0MTcUGfnB359ZnVH3QbZ62FBWGIOz1jf2vTzI6hqmZcVjkk9Yw7NliX5ZNkJ"
}

ALPACA = {
  "key": "PKVQYDYPXE8ENJ437WJA",
  "secret": "WCkGQGybpgg3pehHEhYCd3tP1dq1y7OFGTiitUrr"
}

# TELEGRAM = {
#   "channel": "<CHANEL ID>",
#   "bot": "<BOT KEY HERE>"
# }

print("ENV = ", ENV)