import time

import pytest

from tests.helpers.api_client import create_offer, start_order, finish_order, get_order


@pytest.mark.integration
def test_order_lifecycle():
    offer, token = create_offer("user-1", "scooter-2")
    order = start_order(offer, token)

    time.sleep(1)
    finished = finish_order(order["id"])

    fetched = get_order(order["id"])

    assert finished["finish_time"] is not None
    assert finished["total_amount"] >= 0
    assert fetched["finish_time"] == finished["finish_time"]
