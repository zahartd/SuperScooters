import os

import requests

from app.models import TariffZone, UserProfile, ScooterData, ConfigMap
from app.clients.validate_responses import validate_scooter_data, validate_tariff_zone, validate_user_profile

BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://localhost:3629")

scooter_http = f'{BASE_URL}/scooter-data'
tariff_zone_http = f'{BASE_URL}/tariff-zone-data'
user_http = f'{BASE_URL}/user-profile'
config_http = f'{BASE_URL}/configs'
hold_money_http = f'{BASE_URL}/hold-money-for-order'
clear_money_http = f'{BASE_URL}/clear-money-for-order'


def get_scooter_data(scooter_id: str) -> ScooterData:
    raw_data = requests.get(scooter_http, params={'id': scooter_id})
    if validate_scooter_data(raw_data):
        return ScooterData(id=scooter_id, zone_id=raw_data.json()['zone_id'],
                       charge=int(raw_data.json()['charge']))
    return None

def get_tariff_zone(zone_id: str) -> TariffZone:
    raw_data = requests.get(tariff_zone_http, params={'id': zone_id})
    if validate_tariff_zone(raw_data):
        return TariffZone(id=zone_id,
                      price_per_minute=int(raw_data.json()['price_per_minute']),
                      price_unlock=int(raw_data.json()['price_unlock']),
                      default_deposit=int(raw_data.json()['default_deposit']))
    return None


def get_user_profile(user_id: str) -> UserProfile:
    raw_data = requests.get(user_http, params={'id': user_id})

    if validate_user_profile(raw_data):
        return UserProfile(id=user_id, has_subscribtion=bool(raw_data.json()['has_subscribtion']),
                        trusted=bool(raw_data.json()['trusted']), rides_count=int(raw_data.json()['rides_count']),
                        current_debt=int(raw_data.json()['current_debt']), total_debt=int(raw_data.json()['total_debt']),
                        last_payment_status=raw_data.json()['last_payment_status'])
    return None


def get_configs() -> ConfigMap:
    raw_data = requests.get(config_http)
    return ConfigMap(raw_data.json())


def hold_money_for_order(user_id: str, order_id: str, amount: int):
    for _ in range(3):
        resp = requests.post(hold_money_http,
                    json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
        if resp.status_code == 200:
            break


def clear_money_for_order(user_id: str, order_id: str, amount: int):
    for _ in range(3):
        resp = requests.post(clear_money_http,
                  json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
        if resp.status_code == 200:
            break