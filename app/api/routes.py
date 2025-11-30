from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
import structlog

from app.api.deps import get_connection
from app.api.schemas import OfferRequest, OfferResponse, OfferPayload, OrderResponse, OrderStartRequest
from app.services import offers as offers_service
from app.services import orders as orders_service
from app.static_config import static_config

router = APIRouter()
logger = structlog.get_logger(__name__)

@router.post("/offers", response_model=OfferResponse)
def create_offer(request: OfferRequest):
    logger.info("api: POST /offers", scooter_id=request.scooter_id, user_id=request.user_id)
    result = offers_service.create_offer(request.scooter_id, request.user_id, static_config.clone())
    if isinstance(result, offers_service.CreateOfferError):
        logger.warning("api: create_offer failed", user_id=request.user_id, reason=result.message)
        return OfferResponse(error=result.message)
    offer, token = result
    logger.info("api: create_offer success", offer_id=offer.id, user_id=request.user_id)
    return OfferResponse(offer=OfferPayload.from_dataclass(offer), pricing_token=token)


@router.post("/orders", response_model=OrderResponse)
def create_order(request: OrderStartRequest, conn: Connection = Depends(get_connection)):
    try:
        logger.info(
            "api: POST /orders",
            offer_id=request.offer.id,
            user_id=request.offer.user_id,
            scooter_id=request.offer.scooter_id,
        )
        order = orders_service.start_order(request.offer.to_dataclass(), request.pricing_token, conn, static_config.clone())
    except ValueError as exc:
        logger.warning("api: create_order validation failed", detail=str(exc))
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    logger.info("api: create_order success", order_id=order.id, user_id=order.user_id)
    return OrderResponse.from_dataclass(order)


@router.post("/orders/{order_id}/finish", response_model=OrderResponse)
def finish_order(order_id: str, conn: Connection = Depends(get_connection)):
    try:
        logger.info("api: POST /orders/finish", order_id=order_id)
        order = orders_service.finish_order(order_id, conn, static_config.clone())
    except KeyError:
        logger.warning("api: finish_order not found", order_id=order_id)
        raise HTTPException(status_code=404, detail="order not found")
    logger.info("api: finish_order success", order_id=order_id)
    return OrderResponse.from_dataclass(order)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, conn: Connection = Depends(get_connection)):
    logger.info("api: GET /orders", order_id=order_id)
    order = orders_service.get_order(order_id, conn, static_config.clone())
    if order is None:
        logger.warning("api: get_order not found", order_id=order_id)
        raise HTTPException(status_code=404, detail="order not found")
    logger.info(
        "api: order retrieved successfully",
        order_id=order_id,
        order_status="active" if order.finish_time is None else "finished",
    )
    return OrderResponse.from_dataclass(order)
