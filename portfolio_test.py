import unittest
from portfolio import Portfolio, exchange


class PortfolioTest(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio({'USD': 100})
        self.exchange_fee = 0.01
        self.exchange_rates = {
            'USD': {'BTC': 0.1, 'ETH': 0.5},
            'BTC': {'ETH': 0.01, 'LTC': 20},
            'ETH': {},
            'LTC': {}
        }

    def test_add_negative_amount_of_currency(self):
        with self.assertRaises(ValueError) as ctx:
            self.portfolio.incr_currency('USD', -100)

        self.assertEqual(str(ctx.exception), 'Negative amount')

    def test_decrease_excessive_amount_of_currency(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.portfolio.decr_currency('USD', 101)

        self.assertEqual(str(ctx.exception), 'Insufficient funds')

    def test_decrease_not_exist_currency(self):
        with self.assertRaises(RuntimeError) as ctx:
            self.portfolio.decr_currency('BTC', 1)

        self.assertEqual(str(ctx.exception), 'Insufficient funds')


class ExchangeTest(unittest.TestCase):

    def setUp(self):
        self.portfolio = Portfolio({'USD': 100})
        self.exchange_fee = 0.01
        self.exchange_rates = {
            'USD': {'BTC': 0.1, 'ETH': 0.5},
            'BTC': {'ETH': 0.01, 'LTC': 20},
            'ETH': {},
            'LTC': {},
            'XRP': {}
        }

    def test_to_exchange_with_empty_portfolio(self):
        p = Portfolio({})
        with self.assertRaises(RuntimeError) as ctx:
            exchange(p, self.exchange_rates, self.exchange_fee, 'LTC', 100)

        self.assertEqual(str(ctx.exception), 'You have no currency')

    def test_to_exchange_unreachable_currency(self):
        with self.assertRaises(RuntimeError) as ctx:
            exchange(self.portfolio, self.exchange_rates, self.exchange_fee, 'XRP', 100)

        self.assertEqual(str(ctx.exception), 'No route to XRP')

    def test_to_exchange_when_has_a_negative_cycle_in_rates(self):
        self.exchange_rates = {
            'USD': {'BTC': 1, 'ETH': 4},
            'BTC': {'ETH': 100, 'LTC': 20},
            'ETH': {'BTC': 0.2},
            'LTC': {}
        }

        with self.assertRaises(RuntimeError) as ctx:
            exchange(self.portfolio, self.exchange_rates, self.exchange_fee, 'LTC', 100)

        self.assertEqual(str(ctx.exception), 'Negative cycle detected, cannot find the shortest paths')

    def test_to_exchange_directly(self):
        self.exchange_rates = {
            'USD': {'BTC': 1, 'ETH': 4},
            'BTC': {'ETH': 3},
            'ETH': {},
            'LTC': {}
        }

        exchange(self.portfolio, self.exchange_rates, self.exchange_fee, 'ETH', 10)
        self.assertEqual(float(self.portfolio.currencies['ETH']), 10)
        self.assertEqual(float(self.portfolio.currencies['USD']), 97.47474747474747)

    def test_to_exchange_across_several_currency(self):
        self.exchange_rates = {
            'USD': {'BTC': 1, 'ETH': 4},
            'BTC': {'ETH': 10},
            'ETH': {},
            'LTC': {}
        }

        exchange(self.portfolio, self.exchange_rates, self.exchange_fee, 'ETH', 10)
        self.assertEqual(float(self.portfolio.currencies['ETH']), 10)
        self.assertEqual(float(self.portfolio.currencies['USD']), 98.97969594939292)

    def test_to_exchange_as_many_of_target_currency(self):
        self.exchange_rates = {
            'USD': {'BTC': 1, 'ETH': 4},
            'BTC': {'ETH': 10},
            'ETH': {},
            'LTC': {}
        }

        exchange(self.portfolio, self.exchange_rates, self.exchange_fee, 'ETH', 1000)
        self.assertEqual(float(self.portfolio.currencies['ETH']), 980.1)
        self.assertEqual(float(self.portfolio.currencies['USD']), 0)
