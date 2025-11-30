import os
import time
from typing import Tuple

import requests

API_URL = os.getenv("API_URL", "http://api:8000")


def wait_for_service(url: str, timeout: int = 60) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            resp = requests.get(f"{url}/docs", timeout=2)
            if resp.status_code < 500:
                return
        except requests.RequestException:
            pass
        time.sleep(1)
    raise RuntimeError(f"Service at {url} not ready after {timeout} seconds")


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


def run_scenarios() -> None:
    print("> Starting first scenario! <")
    offer1, token1 = create_offer("some-user-id", "some-scooter-id")
    order1 = start_order(offer1, token1)
    time.sleep(1)
    finish_order(order1["id"])
    print("< First scenario is over!\n")

    print("> Starting second scenario! <")
    offer2, token2 = create_offer("some-user-id", "some-scooter-id")
    order2 = start_order(offer2, token2)
    time.sleep(8)
    finish_order(order2["id"])
    print("< Second scenario is over!\n")


if __name__ == "__main__":
    wait_for_service(API_URL)
    run_scenarios()
