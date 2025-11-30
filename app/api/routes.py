from copy import deepcopy
from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection
import structlog
import time

from app.api.deps import get_connection
from app.api.schemas import OfferRequest, OfferResponse, OfferPayload, OrderResponse, OrderStartRequest
from app.services import offers as offers_service
from app.services import orders as orders_service
from app.static_config import static_config
from app.metrics import METRICS, logger

router = APIRouter()

@router.post("/offers", response_model=OfferResponse)
def create_offer(request: OfferRequest):
    start = time.time()
    offer_calc_start = time.time()
    try:
        logger.info("api: POST /offers", scooter_id=request.scooter_id, user_id=request.user_id)
        result = offers_service.create_offer(request.scooter_id, request.user_id, static_config.clone())
        METRICS['offer_calculation_duration'].observe(time.time() - offer_calc_start)

        if isinstance(result, offers_service.CreateOfferError):
            logger.warning("api: create_offer failed", user_id=request.user_id, reason=result.message)
            METRICS['offer_conversions_total'].labels(status="fail").inc()
            METRICS['api_requests_total'].labels(method="POST", endpoint="/offers", status="400").inc()
            return OfferResponse(error=result.message)

        offer, token = result
        logger.info("api: create_offer success", offer_id=offer.id, user_id=request.user_id)
        METRICS['offer_conversions_total'].labels(status="success").inc()
        METRICS['api_requests_total'].labels(method="POST", endpoint="/offers", status="200").inc()
        return OfferResponse(offer=OfferPayload.from_dataclass(offer), pricing_token=token)
    finally:
        METRICS['api_latency_seconds'].labels(method="POST", endpoint="/offers").observe(time.time() - start)



@router.post("/orders", response_model=OrderResponse)
def create_order(request: OrderStartRequest, conn: Connection = Depends(get_connection)):
    start = time.time()
    try:
        logger.info(
            "api: POST /orders",
            offer_id=request.offer.id,
            user_id=request.offer.user_id,
            scooter_id=request.offer.scooter_id,
        )
        order = orders_service.start_order(
            request.offer.to_dataclass(), request.pricing_token, conn, static_config.clone()
        )
        logger.info("api: create_order success", order_id=order.id, user_id=order.user_id)
        METRICS['api_requests_total'].labels(method="POST", endpoint="/orders", status="200").inc()
        return OrderResponse.from_dataclass(order)
    except ValueError as exc:
        logger.warning("api: create_order validation failed", detail=str(exc))
        METRICS['api_requests_total'].labels(method="POST", endpoint="/orders", status="400").inc()
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    finally:
        METRICS['api_latency_seconds'].labels(method="POST", endpoint="/orders").observe(time.time() - start)


@router.post("/orders/{order_id}/finish", response_model=OrderResponse)
def finish_order(order_id: str, conn: Connection = Depends(get_connection)):
    start = time.time()
    try:
        logger.info("api: POST /orders/finish", order_id=order_id)
        order = orders_service.finish_order(order_id, conn, static_config.clone())
        logger.info("api: finish_order success", order_id=order_id)
        METRICS['api_requests_total'].labels(method="POST", endpoint="/orders/finish", status="200").inc()
        return OrderResponse.from_dataclass(order)
    except KeyError:
        logger.warning("api: finish_order not found", order_id=order_id)
        METRICS['api_requests_total'].labels(method="POST", endpoint="/orders/finish", status="404").inc()
        raise HTTPException(status_code=404, detail="order not found")
    finally:
        METRICS['api_latency_seconds'].labels(method="POST", endpoint="/orders/finish").observe(time.time() - start)

@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, conn: Connection = Depends(get_connection)):
    start = time.time()
    try:
        logger.info("api: GET /orders", order_id=order_id)
        order = orders_service.get_order(order_id, conn, static_config.clone())
        if order is None:
            logger.warning("api: get_order not found", order_id=order_id)
            METRICS['api_requests_total'].labels(method="GET", endpoint="/orders/{order_id}", status="404").inc()
            raise HTTPException(status_code=404, detail="order not found")
        logger.info(
            "api: order retrieved successfully",
            order_id=order_id,
            order_status="active" if order.finish_time is None else "finished",
            from_cache=getattr(order, 'from_cache', False)
        )
        METRICS['api_requests_total'].labels(method="GET", endpoint="/orders/{order_id}", status="200").inc()
        if hasattr(order, 'from_cache'):
            METRICS['cache_hit_ratio'].labels(hit="true" if order.from_cache else "false").inc()
        return OrderResponse.from_dataclass(order)
    finally:
        METRICS['api_latency_seconds'].labels(method="GET", endpoint="/orders/{order_id}").observe(time.time() - start)
