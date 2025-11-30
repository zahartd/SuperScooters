import uuid
from datetime import datetime, timezone

from psycopg import Connection

from app.clients import data_requests as dr
from app.models import ConfigMap, OfferData, OrderData
from app.repository import configs as configs_repo
from app.repository import orders as orders_repo
from app.utils.pricing import validate_pricing_token
import structlog

logger = structlog.get_logger(__name__)
MAGIC_CONSTANT2 = 5


def start_order(offer: OfferData, pricing_token: str, conn: Connection, configs: ConfigMap) -> OrderData:
    configs = configs_repo.get_configs(configs)
    validate_pricing_token(offer, pricing_token, configs)

    logger.info(
        "start_order: validating token",
        offer_id=offer.id,
        user_id=offer.user_id,
        scooter_id=offer.scooter_id,
    )

    order = OrderData(
        str(uuid.uuid4()),
        user_id=offer.user_id,
        scooter_id=offer.scooter_id,
        zone_id=offer.zone_id,
        price_per_minute=offer.price_per_minute,
        price_unlock=offer.price_unlock,
        deposit=offer.deposit,
        total_amount=0,
        start_time=datetime.now(timezone.utc),
        finish_time=None,
    )

    dr.hold_money_for_order(offer.user_id, order.id, offer.deposit)
    logger.debug(
        "start_order: holding deposit",
        user_id=offer.user_id,
        order_id=order.id,
        deposit=offer.deposit,
    )

    orders_repo.insert_order(conn, order)
    logger.info(
        "start_order: created order",
        order_id=order.id,
        user_id=order.user_id,
        scooter_id=order.scooter_id,
        zone_id=order.zone_id,
    )
    return order


def finish_order(order_id: str, conn: Connection, configs: ConfigMap) -> OrderData:
    configs_repo.get_configs(configs)

    order = orders_repo.get_order(conn, order_id)
    if order is None:
        raise KeyError(order_id)

    order.finish_time = datetime.now(timezone.utc)
    duration_sec = (order.finish_time - order.start_time).total_seconds()

    if duration_sec < MAGIC_CONSTANT2:
        dr.clear_money_for_order(order.user_id, order_id, 0)
        logger.info(
            "finish_order: short ride cleared deposit",
            order_id=order_id,
            user_id=order.user_id,
            duration_sec=duration_sec,
        )
    else:
        order.total_amount = (
            int(duration_sec) * order.price_per_minute // 60
            + order.price_unlock
        )
        dr.clear_money_for_order(order.user_id, order_id, order.total_amount)
        logger.info(
            "finish_order: charged",
            order_id=order_id,
            user_id=order.user_id,
            amount=order.total_amount,
            duration_sec=duration_sec,
        )

    orders_repo.update_order_finish(conn, order)
    logger.debug(
        "finish_order: persisted finish",
        order_id=order.id,
        finish_time=order.finish_time,
    )
    return order


def get_order(order_id: str, conn: Connection, configs: ConfigMap) -> OfferData | None:
    logger.debug("get_order: fetching order", order_id=order_id)
    return orders_repo.get_order(conn, order_id)
