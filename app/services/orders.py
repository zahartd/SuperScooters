import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from psycopg import Connection

from app.clients import data_requests as dr
from app.models import OfferData, OrderData
from app.repository import orders as orders_repo
from app.utils.pricing import validate_pricing_token

MAGIC_CONSTANT2 = 5
logger = logging.getLogger(__name__)


def start_order(offer: OfferData, pricing_token: str, conn: Connection) -> OrderData:
    configs = dr.get_configs()
    logger.info(
        "start_order: validating token offer_id=%s user_id=%s scooter_id=%s",
        offer.id,
        offer.user_id,
        offer.scooter_id,
    )
    validate_pricing_token(offer, pricing_token, configs)

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
        "start_order: holding deposit user_id=%s order_id=%s deposit=%s",
        offer.user_id,
        order.id,
        offer.deposit,
    )
    orders_repo.insert_order(conn, order)
    logger.info(
        "start_order: created order order_id=%s user_id=%s scooter_id=%s zone_id=%s",
        order.id,
        order.user_id,
        order.scooter_id,
        order.zone_id,
    )
    return order


def finish_order(order_id: str, conn: Connection) -> OrderData:
    order = orders_repo.get_order(conn, order_id)
    if order is None:
        logger.warning("finish_order: order not found order_id=%s", order_id)
        raise KeyError(order_id)

    order.finish_time = datetime.now(timezone.utc)
    if (order.finish_time - order.start_time).total_seconds() < MAGIC_CONSTANT2:
        dr.clear_money_for_order(order.user_id, order_id, 0)
        logger.info(
            "finish_order: short ride cleared deposit order_id=%s user_id=%s duration_sec=%s",
            order_id,
            order.user_id,
            (order.finish_time - order.start_time).total_seconds(),
        )
    else:
        order.total_amount = (
            int((order.finish_time - order.start_time).total_seconds()) * order.price_per_minute // 60
            + order.price_unlock
        )
        dr.clear_money_for_order(order.user_id, order_id, order.total_amount)
        logger.info(
            "finish_order: charged order_id=%s user_id=%s amount=%s duration_sec=%s",
            order_id,
            order.user_id,
            order.total_amount,
            (order.finish_time - order.start_time).total_seconds(),
        )

    orders_repo.update_order_finish(conn, order)
    logger.debug("finish_order: persisted finish order_id=%s finish_time=%s", order.id, order.finish_time)
    return order


def get_order(order_id: str, conn: Connection) -> Optional[OrderData]:
    logger.debug("get_order: fetching order_id=%s", order_id)
    return orders_repo.get_order(conn, order_id)
