import os

PRODUCTION = "production"
DEVELOPMENT = "development"

COIN_TARGET = "BTC"
COIN_REFER = "USDT"

ENV = os.getenv("ENVIRONMENT", DEVELOPMENT)
DEBUG = True

BINANCE = {
  "key": "U3w1HkCHfEZpzdgEOBdhZDy5pOZmndmwwuJRPQMmimnbMHp69jaWo890wn3EkEv7",
  "secret": "Di4D0MTcUGfnB359ZnVH3QbZ62FBWGIOz1jf2vTzI6hqmZcVjkk9Yw7NliX5ZNkJ"
}

print("ENV = ", ENV)