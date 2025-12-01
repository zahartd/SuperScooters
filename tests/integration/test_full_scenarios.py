import time
import pytest

from tests.helpers.api_client import create_offer, start_order, finish_order, get_order


@pytest.mark.integration
def test_complete_rental_flow_normal_user():
    """Test complete flow: create offer -> start order -> finish order -> verify"""
    offer, token = create_offer("user-1", "scooter-1")
    assert offer["user_id"] == "user-1"
    assert offer["scooter_id"] == "scooter-1"
    assert token
    
    order = start_order(offer, token)
    assert order["id"]
    assert order["finish_time"] is None
    assert order["total_amount"] == 0
    
    time.sleep(6)
    
    finished = finish_order(order["id"])
    assert finished["finish_time"] is not None
    assert finished["total_amount"] > 0
    
    fetched = get_order(order["id"])
    assert fetched["id"] == order["id"]
    assert fetched["finish_time"] == finished["finish_time"]
    assert fetched["total_amount"] == finished["total_amount"]


@pytest.mark.integration
def test_multiple_users_concurrent_rentals():
    """Test multiple users renting different scooters concurrently"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    order1 = start_order(offer1, token1)
    
    offer2, token2 = create_offer("user-4", "scooter-2")
    order2 = start_order(offer2, token2)
    
    time.sleep(2)
    
    finished1 = finish_order(order1["id"])
    finished2 = finish_order(order2["id"])
    
    assert finished1["finish_time"] is not None
    assert finished2["finish_time"] is not None
    assert finished1["id"] != finished2["id"]


@pytest.mark.integration
def test_sequential_rentals_same_scooter():
    """Test that same scooter can be rented sequentially by different users"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    order1 = start_order(offer1, token1)
    time.sleep(1)
    finished1 = finish_order(order1["id"])
    assert finished1["finish_time"] is not None
    
    offer2, token2 = create_offer("user-4", "scooter-1")
    order2 = start_order(offer2, token2)
    time.sleep(1)
    finished2 = finish_order(order2["id"])
    assert finished2["finish_time"] is not None
    
    fetched1 = get_order(order1["id"])
    fetched2 = get_order(order2["id"])
    assert fetched1["scooter_id"] == fetched2["scooter_id"] == "scooter-1"


@pytest.mark.integration
def test_user_high_debt_increased_deposit():
    """Test that users with high debt pay increased deposit"""
    offer, token = create_offer("user-3", "scooter-1")
    
    assert offer["deposit"] == 375
    
    order = start_order(offer, token)
    assert order["deposit"] == 375


@pytest.mark.integration
def test_short_ride_no_charge():
    """Test that very short rides (< 5 seconds) are free"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    time.sleep(2)
    
    finished = finish_order(order["id"])
    assert finished["total_amount"] == 0


@pytest.mark.integration
def test_order_retrieval_multiple_times():
    """Test that order can be retrieved multiple times with same data"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    time.sleep(1)
    finished = finish_order(order["id"])
    
    fetched1 = get_order(order["id"])
    fetched2 = get_order(order["id"])
    fetched3 = get_order(order["id"])
    
    assert fetched1 == fetched2 == fetched3
    assert fetched1["total_amount"] == finished["total_amount"]
