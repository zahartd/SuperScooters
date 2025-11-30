from dataclasses import dataclass

from datetime import datetime


@dataclass
class ScooterData:
    id: str
    zone_id: str
    charge: int


@dataclass
class TariffZone:
    id: str
    price_per_minute: int
    price_unlock: int
    default_deposit: int


@dataclass
class UserProfile:
    id: str
    has_subscribtion: bool
    trusted: bool
    rides_count: int
    current_debt: int
    total_debt: int
    last_payment_status: str


@dataclass
class OfferData:
    id: str
    user_id: str
    scooter_id: str
    zone_id: str
    price_per_minute: int
    price_unlock: int
    deposit: int


@dataclass
class OrderData:
    id: str
    user_id: str
    scooter_id: str
    zone_id: str
    price_per_minute: int
    price_unlock: int
    deposit: int
    total_amount: int
    start_time: datetime
    finish_time: datetime


@dataclass
class PricingTokenPayload:
    user_id: str
    expires_at: str
    tariff_version: str
    pricing_algo_version: str
    offer_hash: str


class ConfigMap:
    def __init__(self, data: dict):
        self._data = data
        for k, v in data.items():
            self.__setattr__(k, v)

    def __getattr__(self, item):
        return self._data.get(item, None)
    
    def merge(self, other: 'ConfigMap'):
        self._data.update(other._data)
    
    def clone(self):
        return ConfigMap(self._data.copy())
