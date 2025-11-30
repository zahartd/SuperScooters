import time
import pytest

from tests.helpers.api_client import create_offer, start_order, finish_order


@pytest.mark.integration
def test_order_very_short_ride_free():
    """Orders shorter than 5 seconds should be free"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    # Wait less than 5 seconds
    time.sleep(1)
    
    finished = finish_order(order["id"])
    
    assert finished["total_amount"] == 0
    assert finished["finish_time"] is not None


@pytest.mark.integration
def test_order_pricing_calculation():
    """Order pricing should be calculated correctly based on duration"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    # Wait more than 5 seconds
    time.sleep(6)
    
    finished = finish_order(order["id"])
    
    # Should charge price_unlock + duration * price_per_minute
    expected_minimum = order["price_unlock"]
    assert finished["total_amount"] >= expected_minimum
    assert finished["total_amount"] > 0


@pytest.mark.integration
def test_order_preserves_offer_pricing():
    """Order should preserve the pricing from the offer"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    assert order["price_per_minute"] == offer["price_per_minute"]
    assert order["price_unlock"] == offer["price_unlock"]
    assert order["deposit"] == offer["deposit"]
    assert order["zone_id"] == offer["zone_id"]


@pytest.mark.integration
def test_order_initial_total_amount_zero():
    """New orders should have total_amount of 0"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    assert order["total_amount"] == 0


@pytest.mark.integration
def test_multiple_orders_different_users():
    """Multiple users should be able to create orders simultaneously"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    offer2, token2 = create_offer("user-4", "scooter-2")
    
    order1 = start_order(offer1, token1)
    order2 = start_order(offer2, token2)
    
    assert order1["id"] != order2["id"]
    assert order1["user_id"] == "user-1"
    assert order2["user_id"] == "user-4"


@pytest.mark.integration
def test_order_finish_time_after_start_time():
    """Finished order should have finish_time after start_time"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    time.sleep(1)
    finished = finish_order(order["id"])
    
    # Both should be ISO format timestamps
    assert finished["start_time"] < finished["finish_time"]

