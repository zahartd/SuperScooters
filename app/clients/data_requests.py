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
    raw_data = requests.get(scooter_http, params={'id': scooter_id}).json()
    return ScooterData(id=scooter_id, zone_id=raw_data.get('zone_id', ''),
                       charge=int(raw_data.get('charge', 0)))

def get_tariff_zone(zone_id: str) -> TariffZone:
    raw_data = requests.get(tariff_zone_http, params={'id': zone_id}).json()
    return TariffZone(id=zone_id,
                      price_per_minute=int(raw_data.get('price_per_minute', 0)),
                      price_unlock=int(raw_data.get('price_unlock', 0)),
                      default_deposit=int(raw_data.get('default_deposit', 0)))


def get_user_profile(user_id: str) -> UserProfile:
    raw_data = requests.get(user_http, params={'id': user_id}).json()

    return UserProfile(id=user_id, has_subscribtion=bool(raw_data.get('has_subscribtion', False)),
                       trusted=bool(raw_data.get('trusted', False)), rides_count=int(raw_data.get('rides_count', 0)),
                       current_debt=int(raw_data.get('current_debt', 0)), total_debt=int(raw_data.get('total_debt', 0)),
                       last_payment_status=raw_data.get('last_payment_status', ''))


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