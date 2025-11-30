import time
import pytest

from tests.helpers.api_client import create_offer, start_order, finish_order, get_order


@pytest.mark.integration
def test_get_order_before_finish():
    """Should be able to get order details before it's finished"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    fetched = get_order(order["id"])
    
    assert fetched["id"] == order["id"]
    assert fetched["finish_time"] is None
    assert fetched["total_amount"] == 0


@pytest.mark.integration
def test_get_order_after_finish():
    """Should be able to get order details after it's finished"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    time.sleep(1)
    finished = finish_order(order["id"])
    
    fetched = get_order(order["id"])
    
    assert fetched["id"] == order["id"]
    assert fetched["finish_time"] == finished["finish_time"]
    assert fetched["total_amount"] == finished["total_amount"]


@pytest.mark.integration
def test_order_sequence_for_same_user():
    """User should be able to complete multiple orders in sequence"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    order1 = start_order(offer1, token1)
    time.sleep(1)
    finished1 = finish_order(order1["id"])
    
    offer2, token2 = create_offer("user-1", "scooter-2")
    order2 = start_order(offer2, token2)
    time.sleep(1)
    finished2 = finish_order(order2["id"])
    
    assert finished1["id"] != finished2["id"]
    assert finished1["user_id"] == finished2["user_id"] == "user-1"


@pytest.mark.integration
def test_order_preserves_user_and_scooter_ids():
    """Order should preserve user_id and scooter_id from offer"""
    offer, token = create_offer("user-4", "scooter-5")
    order = start_order(offer, token)
    
    assert order["user_id"] == offer["user_id"] == "user-4"
    assert order["scooter_id"] == offer["scooter_id"] == "scooter-5"


@pytest.mark.integration
def test_order_id_is_unique():
    """Each order should have a unique ID"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    offer2, token2 = create_offer("user-1", "scooter-1")
    
    order1 = start_order(offer1, token1)
    order2 = start_order(offer2, token2)
    
    assert order1["id"] != order2["id"]


@pytest.mark.integration
def test_order_total_amount_increases_with_time():
    """Longer rides should cost more than shorter rides"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    order1 = start_order(offer1, token1)
    time.sleep(6)
    finished1 = finish_order(order1["id"])
    
    offer2, token2 = create_offer("user-1", "scooter-2")
    order2 = start_order(offer2, token2)
    time.sleep(10)
    finished2 = finish_order(order2["id"])
    
    if order1["price_per_minute"] == order2["price_per_minute"]:
        assert finished2["total_amount"] >= finished1["total_amount"]


@pytest.mark.integration
def test_order_start_time_is_set():
    """Order should have start_time set when created"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    assert "start_time" in order
    assert order["start_time"] is not None
    assert "T" in order["start_time"]
