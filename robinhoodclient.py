import requests
import json
import sys
import getpass

class RobinhoodClient(object):
    api_url = 'https://api.robinhood.com'

    def __init__(self, token=None):
        self.token = token

    def login(self):
        username = raw_input("Username: ")
        password = getpass.getpass("Password: ")
        request = {
            'username': username,
            'password': password
        }
        def _login_api_call():
            try:
                response = requests.post(self.api_url + '/api-token-auth/', data=request, headers=self._headers())
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                print e
                sys.exit(1)
            return json.loads(response.text)

        response = _login_api_call()
        if 'mfa_required' in response:
            request['mfa_code'] = raw_input("Enter code: ")
            response = _login_api_call()
        self.token = response['token']
        print "Successfully logged in as {}".format(username)

    def logout(self):
        response = requests.post(self.api_url + '/api-token-logout/', data={}, headers=self._headers())
        if response.status_code == 200:
            return {}
        else:
            return json.loads(response.text)

    def order(self, account, instrument, symbol, order_type, time_in_force, trigger, quantity, side, price=None, stop_price=None, extended_hours=False):
        """Buy or sell a security.

        :param account: account url
        :param instrument: instrument url
        :param symbol: security ticker
        :param order_type: 'market' or 'limit'
        :param time_in_force: 'gfd', 'gtc', 'ioc', 'fok', or 'opg'
        :param trigger: 'immediate' or 'stop'
        :type quantity: int
        :param side: 'buy' or 'sell'
        :param price: valid only if `order_type` is "limit"
        :type price: float
        :param stop_price: valid only if `trigger` is "stop"
        :type stop_price: float
        :param extended_hours: if order should execute when exchanges are closed

        Response schema: see order_info()

        """
        request = {
            'account': account,
            'instrument': instrument,
            'symbol': symbol,
            'type': order_type,
            'time_in_force': time_in_force,
            'trigger': trigger,
            'quantity': quantity,
            'side': side,
        }
        if order_type == 'limit':
            request['price'] = price
        if trigger == 'stop':
            request['stop_price'] = stop_price
        if extended_hours:
            request['extended_hours'] = extended_hours
        response = requests.post(self.api_url + '/orders/', data=request, headers=self._headers())
        return json.loads(response.text)

    def order_info(self, order_id):
        """Gets order info. Response schema:

        'updated_at': iso8601utc
        'created_at': iso8601utc
        'last_transaction_at': iso8601utc
        'executions': list
        'id': string
        'quantity': string (number of shares for order)
        'cumulative_quantity': string (number of shares executed)
        'price': string | null (price of order if limit)
        'side': string (buy or sell)
        'state': string (queued, unconfirmed, confirmed, partially_filled, filled, rejected, canceled, or failed)
        'url': string (url for /orders/{order_id}/)
        'cancel': string (url for /orders/{order_id}/cancel/)
        'instrument': string (url to get more security info)
        'account': string (url for account)

        """
        response = requests.get(self.api_url + '/orders/' + order_id + '/', headers=self._headers())
        return json.loads(response.text)

    def order_recents(self):
        """Gets past 100 recent orders. Response schema:

        'next': string (url for cursor. paginated)
        'previous': string (url for cursor. paginated)
        'results': list (see order_info for schema of each object)

        """
        response = requests.get(self.api_url + '/orders/', headers=self._headers())
        return json.loads(response.text)

    def order_cancel(self, order_id):
        """Cancels an order. Response is {} on success"""
        response = requests.post(self.api_url + '/orders/' + order_id + '/cancel/', headers=self._headers())
        return json.loads(response.text)

    def account_info(self):
        """Gets account information. Response schema:

        'results': list (list of accounts)
            'account_number': string (acts as id. append to /accounts/)
            'url': string (url for /accounts/{account_number})
            'positions': string (url for /accounts/{account_number}/positions/)
            'portfolio': string (url for /accounts/{account_number}/portfolio/)
            'buying_power': string (if RH gold, this value is inaccurate)
            'cash': string (including unsettled funds)
            'cash_held_for_orders': string (if RH gold, this value is inaccurate)
            'unsettled_funds': string
            'updated_at': iso8601utc
            
            if subscribed to RH gold, this is null
            'cash_balances': { 
                'buying_power': string
            }

            if not subscribed to RH gold, this is null
            'margin_balances': {
                'unallocated_margin_cash': string (buying power)
                'cash_held_for_orders': string
            }

        """
        response = requests.get(self.api_url + '/accounts/', headers=self._headers())
        res = json.loads(response.text)
        self.account_number = res['results'][0]['account_number']
        return res

    def account_position(instrument_id):
        """Gets account position for the instrument. Response schema:

        'account': string (url for /accounts/{account_number}/)
        'average_buy_price': string
        'created_at': iso8601utc
        'updated_at': iso8601utc
        'instrument': string (url for instrument)
        'quantity': string
        'shares_held_for_buys': string
        'shares_held_for_sells': string
        'url': string (url for /accounts/{account_number}/positions/{instrument_id}/)

        """
        response = requests.get(self.api_url + '/accounts/' + self.account_number + '/positions/' + instrument_id + '/', headers=self._headers())
        return json.loads(response.text)

    def account_positions(self):
        """Gets entire account position history. Response schema:

        'next': string (pagination url)
        'previous': string (pagination url)
        'results': list (see account_position() for schema of each object)

        """
        response = requests.get(self.api_url + '/accounts/' + self.account_number + '/positions/', headers=self._headers())
        return json.loads(response.text)

    def portfolio_info(self):
        """Gets account portfolio. Response schema:

        'start_date': string (YYYY-MM-DD when you first started trading!)
        'account': string (account url /accounts/{account_number})
        'equity_previous_close': string
        'equity': string (amount of money in securities + cash)
        'market_value': string (amount of money in securities)
        'extended_hours_equity': string
        'extended_hours_equity_market_value': string

        """
        response = requests.get(self.api_url + '/accounts' + self.account_number + '/portfolio/', headers=self._headers())
        return json.loads(response.text)

    def user_info(self):
        """Gets basic user info. Response schema:

        'username': string
        'first_name': string
        'last_name': string

        """
        response = requests.get(self.api_url + '/user/', headers=self._headers())
        return json.loads(response.text)

    def instrument(self, ticker):
        """Gets a financial instrument of a single ticker. Response schema:

        'url': string (endpoint to get more info about this security)
        'symbol': string (ticker)
        'id': string (note: appended to /instruments/)
        'name': string (security display name)
        'qoute': string (url for quote info)
        'fundamentals': string (url for fundamentals)

        """
        response = requests.get(self.api_url + '/instruments/?symbol=' + ticker)
        return json.loads(response.text)

    def quotes(self, tickers):
        """Gets quote data for a list of tickers. Response schema:

        'results': list (list of quote data for each ticker)
            'ask_price': string
            'ask_size': int
            'bid_price': string
            'bid_size': int
            'last_trade_price': string
            'last_extended_hours_trade_price': string | null
            'previous_close': string
            'updated_at': iso8601utc

        """
        response = requests.get(self.api_url + '/quotes/?symbols=' + ','.join(tickers))
        return json.loads(response.text)

    def fundamentals(self, tickers):
        """Gets fundamental data for a list of tickers. Response schema:

        'results': list (list of fundamental data for each ticker)
            'open': float
            'high': float
            'low': float
            'volume': float
            'instrument': string (url to get more information on the security)
        """
        response = requests.get(self.api_url + '/fundamentals/?symbols=' + ','.join(tickers))
        return json.loads(response.text)

    def _headers(self):
        headers = {
            'Accept': 'application/json; charset=utf-8',
        }
        if self.token:
            headers['Authorization'] = 'Token ' + self.token
        return headers