from fastapi import APIRouter, Depends, HTTPException
from psycopg import Connection

from app.api.deps import get_connection
from app.api.schemas import OfferRequest, OfferResponse, OfferPayload, OrderResponse, OrderStartRequest
from app.services import offers as offers_service
from app.services import orders as orders_service

router = APIRouter()


@router.post("/offers", response_model=OfferResponse)
def create_offer(request: OfferRequest):
    offer, token = offers_service.create_offer(request.scooter_id, request.user_id)
    return OfferResponse(offer=OfferPayload.from_dataclass(offer), pricing_token=token)


@router.post("/orders", response_model=OrderResponse)
def create_order(request: OrderStartRequest, conn: Connection = Depends(get_connection)):
    try:
        order = orders_service.start_order(request.offer.to_dataclass(), request.pricing_token, conn)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return OrderResponse.from_dataclass(order)


@router.post("/orders/{order_id}/finish", response_model=OrderResponse)
def finish_order(order_id: str, conn: Connection = Depends(get_connection)):
    try:
        order = orders_service.finish_order(order_id, conn)
    except KeyError:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderResponse.from_dataclass(order)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, conn: Connection = Depends(get_connection)):
    order = orders_service.get_order(order_id, conn)
    if order is None:
        raise HTTPException(status_code=404, detail="order not found")
    return OrderResponse.from_dataclass(order)
