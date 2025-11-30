from dataclasses import asdict
from typing import Optional

from pydantic import BaseModel

from app.models import OfferData, OrderData


class OfferRequest(BaseModel):
    scooter_id: str
    user_id: str


class OfferPayload(BaseModel):
    id: str
    user_id: str
    scooter_id: str
    zone_id: str
    price_per_minute: int
    price_unlock: int
    deposit: int

    @classmethod
    def from_dataclass(cls, offer: OfferData) -> "OfferPayload":
        return cls(**asdict(offer))

    def to_dataclass(self) -> OfferData:
        return OfferData(**self.model_dump())


class OfferResponse(BaseModel):
    offer: OfferPayload | None
    pricing_token: str | None
    error: str | None


class OrderStartRequest(BaseModel):
    offer: OfferPayload
    pricing_token: str


class OrderResponse(BaseModel):
    id: str
    user_id: str
    scooter_id: str
    zone_id: str
    price_per_minute: int
    price_unlock: int
    deposit: int
    total_amount: int
    start_time: str
    finish_time: Optional[str] = None

    @classmethod
    def from_dataclass(cls, order: OrderData) -> "OrderResponse":
        payload = asdict(order)
        payload["start_time"] = order.start_time.isoformat()
        payload["finish_time"] = order.finish_time.isoformat() if order.finish_time else None
        return cls(**payload)
