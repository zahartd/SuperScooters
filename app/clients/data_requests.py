import os
import requests
import structlog
import time

from app.models import TariffZone, UserProfile, ScooterData, ConfigMap
from app.metrics import METRICS, measure_external_call

BASE_URL = os.environ.get("EXTERNAL_BASE_URL", "http://localhost:3629")

scooter_http = f'{BASE_URL}/scooter-data'
tariff_zone_http = f'{BASE_URL}/tariff-zone-data'
user_http = f'{BASE_URL}/user-profile'
config_http = f'{BASE_URL}/configs'
hold_money_http = f'{BASE_URL}/hold-money-for-order'
clear_money_http = f'{BASE_URL}/clear-money-for-order'

logger = structlog.get_logger(__name__)


@measure_external_call("get_scooter_data")
def get_scooter_data(scooter_id: str) -> ScooterData:
    logger.debug("data_requests: fetching scooter data", scooter_id=scooter_id, url=scooter_http)
    raw_data = requests.get(scooter_http, params={'id': scooter_id}).json()
    logger.debug("data_requests: fetched scooter data", scooter_id=scooter_id, data=raw_data)
    return ScooterData(id=scooter_id, zone_id=raw_data.get('zone_id', ''),
                       charge=int(raw_data.get('charge', 0)))


@measure_external_call("get_tariff_zone")
def get_tariff_zone(zone_id: str) -> TariffZone:
    logger.debug("data_requests: fetching tariff zone data", zone_id=zone_id, url=tariff_zone_http)
    raw_data = requests.get(tariff_zone_http, params={'id': zone_id}).json()
    logger.debug("data_requests: fetched tariff zone data", zone_id=zone_id, data=raw_data)
    return TariffZone(id=zone_id,
                      price_per_minute=int(raw_data.get('price_per_minute', 0)),
                      price_unlock=int(raw_data.get('price_unlock', 0)),
                      default_deposit=int(raw_data.get('default_deposit', 0)))


@measure_external_call("get_user_profile")
def get_user_profile(user_id: str) -> UserProfile:
    logger.debug("data_requests: fetching user profile", user_id=user_id, url=user_http)
    raw_data = requests.get(user_http, params={'id': user_id}).json()
    logger.debug("data_requests: fetched user profile", user_id=user_id, data=raw_data)
    return UserProfile(
        id=user_id,
        has_subscribtion=bool(raw_data.get('has_subscribtion', False)),
        trusted=bool(raw_data.get('trusted', False)),
        rides_count=int(raw_data.get('rides_count', 0)),
        current_debt=int(raw_data.get('current_debt', 0)),
        total_debt=int(raw_data.get('total_debt', 0)),
        last_payment_status=raw_data.get('last_payment_status', '')
    )


@measure_external_call("get_configs")
def get_configs() -> ConfigMap:
    logger.debug("data_requests: fetching configs", url=config_http)
    raw_data = requests.get(config_http)
    logger.debug("data_requests: fetched configs", data=raw_data.json())
    return ConfigMap(raw_data.json())


@measure_external_call("hold_money")
def hold_money_for_order(user_id: str, order_id: str, amount: int):
    logger.info("data_requests: holding money for order", user_id=user_id, order_id=order_id, amount=amount)

    for _ in range(3):
        start = time.time()
        resp = requests.post(
            hold_money_http,
            json={'user_id': user_id, 'order_id': order_id, 'amount': amount}
        )
        duration = time.time() - start

        logger.debug(
            "data_requests: hold money attempt",
            status_code=resp.status_code,
            duration_ms=round(duration * 1000, 2),
            attempt=_ + 1
        )

        if resp.status_code == 200:
            METRICS["payment_hold_success_total"].inc()
            logger.info(
                "data_requests: money hold success",
                user_id=user_id,
                order_id=order_id,
                amount=amount,
                duration_ms=round(duration * 1000, 2)
            )
            return

        METRICS["payment_failures_total"].labels(reason="hold_failed").inc()
        logger.warning(
            "data_requests: money hold failed",
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            status_code=resp.status_code,
            attempt=_ + 1
        )

@measure_external_call("clear_money")
def clear_money_for_order(user_id: str, order_id: str, amount: int):
    logger.info("data_requests: clearing money for order", user_id=user_id, order_id=order_id, amount=amount)

    for _ in range(3):
        start = time.time()
        resp = requests.post(
            clear_money_http,
            json={'user_id': user_id, 'order_id': order_id, 'amount': amount}
        )
        duration = time.time() - start

        logger.debug(
            "data_requests: clear money attempt",
            status_code=resp.status_code,
            duration_ms=round(duration * 1000, 2),
            attempt=_ + 1
        )

        if resp.status_code == 200:
            METRICS["payment_clear_success_total"].inc()
            logger.info(
                "data_requests: money clear success",
                user_id=user_id,
                order_id=order_id,
                amount=amount,
                duration_ms=round(duration * 1000, 2)
            )
            return

        METRICS["payment_failures_total"].labels(reason="clear_failed").inc()
        logger.warning(
            "data_requests: money clear failed",
            user_id=user_id,
            order_id=order_id,
            amount=amount,
            status_code=resp.status_code,
            attempt=_ + 1
        )

