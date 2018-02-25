import copy
import numpy as np
from decimal import Decimal
from bellman_ford import bellman_ford


class Portfolio(object):
    def __init__(self, currencies):
        self.currencies = currencies

    def incr_currency(self, name, amount):
        if amount < 0:
            raise ValueError('Negative amount')

        if name in self.currencies:
            self.currencies[name] += amount
        else:
            self.currencies[name] = amount

    def decr_currency(self, name, amount):
        if name not in self.currencies or self.currencies[name] < amount:
            raise RuntimeError('Insufficient funds')

        self.currencies[name] -= amount


def _append_exchange_fee(rates, fee_in_percentage):
    rates_copy = copy.deepcopy(rates)
    for _, values in rates_copy.items():
        for name, rate in values.items():
            values[name] = rate * (1 - fee_in_percentage)

    return rates_copy


def _transform(rates):
    rates_copy = copy.deepcopy(rates)
    for _, values in rates_copy.items():
        for name, rate in values.items():
            values[name] = -np.log(rate)

    return rates_copy


def _build_route(predecessor, source, target):
    route = [target]
    while route[0] != source:
        target = predecessor[route[0]]
        route.insert(0, target)

    return route


def _find_shortest_path(portfolio, target_currency, transformed_rates):
    source_currency = None
    final_predecessor = None
    shortest_distance = float('Inf')
    for name, amount in portfolio.currencies.items():
        if name == target_currency:
            continue

        distance, predecessor = bellman_ford(transformed_rates, name)
        if distance[target_currency] < shortest_distance:
            shortest_distance = distance[target_currency]
            final_predecessor = predecessor
            source_currency = name

    if source_currency is None:
        raise RuntimeError('No route to {}'.format(target_currency))

    route = _build_route(final_predecessor, source_currency, target_currency)
    return source_currency, route


def _calculate_full_route_rate(route, rates):
    route_copy = copy.deepcopy(route)
    full_route_rate = 1
    while len(route_copy) > 1:
        _from = route_copy[-2]
        _to = route_copy[-1]

        full_route_rate = Decimal(full_route_rate) * Decimal(rates[_from][_to])
        route_copy.remove(_to)

    return full_route_rate


def exchange(portfolio, rates, fee, target_currency, amount):
    if len(portfolio.currencies) == 0:
        raise RuntimeError('You have no currency')

    fee_included_rates = _append_exchange_fee(rates, fee)
    transformed_rates = _transform(fee_included_rates)

    source_currency, route = _find_shortest_path(portfolio, target_currency, transformed_rates)
    full_route_rate = _calculate_full_route_rate(route, fee_included_rates)

    max_exchange_amount = Decimal(portfolio.currencies[source_currency]) * Decimal(full_route_rate)
    if amount > max_exchange_amount:
        currency_cost = portfolio.currencies[source_currency]
    else:
        currency_cost = Decimal(amount) / Decimal(full_route_rate)

    while len(route) > 1:
        _from = route[0]
        _to = route[1]
        _rate = fee_included_rates[_from][_to]
        _exchange_amount = Decimal(currency_cost) * Decimal(_rate)

        portfolio.decr_currency(_from, currency_cost)
        portfolio.incr_currency(_to, _exchange_amount)
        print('Exchanged {} {} to {} {}'.format(currency_cost, _from, _exchange_amount, _to))

        currency_cost = _exchange_amount
        route.remove(_from)
