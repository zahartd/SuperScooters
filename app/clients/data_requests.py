import logging
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
logger = logging.getLogger(__name__)


def get_scooter_data(scooter_id: str) -> ScooterData:
    logger.debug("data_requests: fetching scooter data scooter_id=%s url=%s", scooter_id, scooter_http)
    raw_data = requests.get(scooter_http, params={'id': scooter_id})
    logger.debug("data_requests: scooter response status=%s", raw_data.status_code)

    # TODO: error handling
    # TODO: data parsing

    payload = raw_data.json()
    return ScooterData(id=scooter_id, zone_id=payload['zone_id'], charge=int(payload['charge']))

def get_tariff_zone(zone_id: str) -> TariffZone:
    logger.debug("data_requests: fetching tariff zone zone_id=%s url=%s", zone_id, tariff_zone_http)
    raw_data = requests.get(tariff_zone_http, params={'id': zone_id})
    logger.debug("data_requests: tariff response status=%s", raw_data.status_code)

    # TODO: error handling
    # TODO: data parsing

    payload = raw_data.json()
    return TariffZone(
        id=zone_id,
        price_per_minute=int(payload['price_per_minute']),
        price_unlock=int(payload['price_unlock']),
        default_deposit=int(payload['default_deposit']),
    )


def get_user_profile(user_id: str) -> UserProfile:
    logger.debug("data_requests: fetching user profile user_id=%s url=%s", user_id, user_http)
    raw_data = requests.get(user_http, params={'id': user_id})
    logger.debug("data_requests: user response status=%s", raw_data.status_code)

    # TODO: error handling
    # TODO: data parsing

    payload = raw_data.json()
    return UserProfile(
        id=user_id,
        has_subscribtion=bool(payload['has_subscribtion']),
        trusted=bool(payload['trusted']),
        rides_count=int(payload['rides_count']),
        current_debt=int(payload['current_debt']),
        total_debt=int(payload['total_debt']),
        last_payment_status=payload['last_payment_status'],
    )


def get_configs() -> ConfigMap:
    logger.debug("data_requests: fetching configs url=%s", config_http)
    raw_data = requests.get(config_http)
    logger.debug("data_requests: configs response status=%s", raw_data.status_code)

    # TODO: error handling

    return ConfigMap(raw_data.json())


def hold_money_for_order(user_id: str, order_id: str, amount: int):
    logger.info(
        "data_requests: hold money user_id=%s order_id=%s amount=%s url=%s",
        user_id,
        order_id,
        amount,
        hold_money_http,
    )
    requests.post(hold_money_http, json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
    # TODO: error handling


def clear_money_for_order(user_id: str, order_id: str, amount: int):
    logger.info(
        "data_requests: clear money user_id=%s order_id=%s amount=%s url=%s",
        user_id,
        order_id,
        amount,
        clear_money_http,
    )
    requests.post(clear_money_http, json={'user_id': user_id, 'order_id': order_id, 'amount': amount})
    # TODO: error handling
