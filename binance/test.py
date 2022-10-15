import requests, json


BASE_URL = 'https://testnet.binancefuture.com'

api_key = 'da51a0215dcd37067647b257431864b88b98b56b6336ffd9245ab8feaa368bc3'
api_secret = '2c9936cf4403eff15895fde2ec1ae0a532c159f8aa96a38149f97e3aa86316b4'

HEADERS = {
    'HMAC' : api_key,
    'SHA256': api_secret
}


ACCOUNT_URL = '{}/fapi/v1/klines'.format(BASE_URL)


def get_account():
    r = requests.get(ACCOUNT_URL, headers=HEADERS)
    return json.loads(r.content)

print(get_account())
