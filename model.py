from dataclasses import dataclass

from datetime import datetime


# Содержит в себе DTO (data transfer objects) / данные, получаемые из внешних источников


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
    price_per_minute: int
    price_unlock: int
    deposit: int
    total_amount: int
    start_time: datetime
    finish_time: datetime


class ConfigMap:
    def __init__(self, data: dict):
        self._data = data
        for k, v in data.items():
            self.__setattr__(k, v)

    def __getattr__(self, item):
        return self._data.get(item, None)
