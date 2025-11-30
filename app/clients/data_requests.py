import os

import requests

from app.models import TariffZone, UserProfile, ScooterData, ConfigMap

BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://localhost:3629")

scooter_http = f'{BASE_URL}/scooter-data'
tariff_zone_http = f'{BASE_URL}/tariff-zone-data'
user_http = f'{BASE_URL}/user-profile'
config_http = f'{BASE_URL}/configs'
hold_money_http = f'{BASE_URL}/hold-money-for-order'
clear_money_http = f'{BASE_URL}/clear-money-for-order'


def get_scooter_data(scooter_id: str) -> ScooterData:
    raw_data = requests.get(scooter_http, params={'id': scooter_id})

    # TODO: error handling
    # TODO: data parsing

    return ScooterData(id=scooter_id, zone_id=raw_data.json()['zone_id'],
                       charge=int(raw_data.json()['charge']))

def get_tariff_zone(zone_id: str) -> TariffZone:
    raw_data = requests.get(tariff_zone_http, params={'id': zone_id})

    # TODO: error handling
    # TODO: data parsing

    return TariffZone(id=zone_id,
                      price_per_minute=int(raw_data.json()['price_per_minute']),
                      price_unlock=int(raw_data.json()['price_unlock']),
                      default_deposit=int(raw_data.json()['default_deposit']))


def get_user_profile(user_id: str) -> UserProfile:
    raw_data = requests.get(user_http, params={'id': user_id})

    # TODO: error handling
    # TODO: data parsing

    return UserProfile(id=user_id, has_subscribtion=bool(raw_data.json()['has_subscribtion']),
                       trusted=bool(raw_data.json()['trusted']), rides_count=int(raw_data.json()['rides_count']),
                       current_debt=int(raw_data.json()['current_debt']), total_debt=int(raw_data.json()['total_debt']),
                       last_payment_status=raw_data.json()['last_payment_status'])


def get_configs() -> ConfigMap:
    raw_data = requests.get(config_http)

    # TODO: error handling

    return ConfigMap(raw_data.json())


def hold_money_for_order(user_id: str, order_id: str, amount: int):
    requests.post(hold_money_http,
                  json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
    # TODO: error handling


def clear_money_for_order(user_id: str, order_id: str, amount: int):
    requests.post(clear_money_http,
                  json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
    # TODO: error handling
