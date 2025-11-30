import os
from typing import Tuple

import requests

API_URL = os.getenv("API_URL", "http://api:8000")


def create_offer(user_id: str, scooter_id: str) -> Tuple[dict, str]:
    resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": user_id, "scooter_id": scooter_id},
        timeout=5,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["offer"], data["pricing_token"]


def start_order(offer: dict, token: str) -> dict:
    resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": offer, "pricing_token": token},
        timeout=5,
    )
    resp.raise_for_status()
    return resp.json()


def finish_order(order_id: str) -> dict:
    resp = requests.post(f"{API_URL}/orders/{order_id}/finish", timeout=5)
    resp.raise_for_status()
    return resp.json()


def get_order(order_id: str) -> dict:
    resp = requests.get(f"{API_URL}/orders/{order_id}", timeout=5)
    resp.raise_for_status()
    return resp.json()
