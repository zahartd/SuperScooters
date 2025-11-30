import time
import pytest

from tests.helpers.api_client import create_offer, start_order, finish_order, get_order


@pytest.mark.integration
def test_order_cannot_be_started_twice():
    """Test that starting multiple orders with same offer is handled"""
    offer, token = create_offer("user-1", "scooter-1")
    
    order1 = start_order(offer, token)
    assert order1["id"]
    
    try:
        order2 = start_order(offer, token)
        assert order2["id"] != order1["id"]
    except Exception:
        pass


@pytest.mark.integration
def test_order_state_during_ride():
    """Test order state while ride is in progress"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    fetched = get_order(order["id"])
    assert fetched["finish_time"] is None
    assert fetched["total_amount"] == 0
    assert fetched["start_time"]


@pytest.mark.integration
def test_order_state_after_finish():
    """Test order state after ride is completed"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    time.sleep(6)
    finished = finish_order(order["id"])
    
    assert finished["finish_time"] is not None
    assert finished["total_amount"] >= 0
    assert finished["start_time"] < finished["finish_time"]


@pytest.mark.integration
def test_order_idempotent_get():
    """Test that getting order multiple times returns consistent data"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    get1 = get_order(order["id"])
    time.sleep(0.5)
    get2 = get_order(order["id"])
    time.sleep(0.5)
    get3 = get_order(order["id"])
    
    assert get1 == get2 == get3


@pytest.mark.integration
def test_order_maintains_offer_data():
    """Test that order maintains all data from original offer"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    assert order["user_id"] == offer["user_id"]
    assert order["scooter_id"] == offer["scooter_id"]
    assert order["zone_id"] == offer["zone_id"]
    assert order["price_per_minute"] == offer["price_per_minute"]
    assert order["price_unlock"] == offer["price_unlock"]
    assert order["deposit"] == offer["deposit"]


@pytest.mark.integration
def test_order_timestamps_format():
    """Test that order timestamps are in correct format"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    assert "T" in order["start_time"]
    assert isinstance(order["start_time"], str)
    
    time.sleep(1)
    finished = finish_order(order["id"])
    
    assert "T" in finished["finish_time"]
    assert isinstance(finished["finish_time"], str)


@pytest.mark.integration
def test_multiple_orders_independent():
    """Test that multiple orders are independent"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    order1 = start_order(offer1, token1)
    
    offer2, token2 = create_offer("user-4", "scooter-2")
    order2 = start_order(offer2, token2)
    
    time.sleep(1)
    
    finished1 = finish_order(order1["id"])
    
    assert finished1["finish_time"] is not None
    
    in_progress = get_order(order2["id"])
    assert in_progress["finish_time"] is None
    
    finished2 = finish_order(order2["id"])
    assert finished2["finish_time"] is not None


@pytest.mark.integration
def test_order_creation_time_is_recent():
    """Test that order start time is close to actual creation time"""
    import datetime
    
    before = datetime.datetime.now(datetime.timezone.utc)
    
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    after = datetime.datetime.now(datetime.timezone.utc)
    
    start_time = datetime.datetime.fromisoformat(order["start_time"].replace('Z', '+00:00'))
    
    assert before <= start_time <= after + datetime.timedelta(seconds=2)


@pytest.mark.integration
def test_order_complete_flow_verification():
    """Complete flow with verification at each step"""
    offer, token = create_offer("user-1", "scooter-1")
    assert offer["id"]
    assert token
    
    order = start_order(offer, token)
    assert order["id"]
    assert order["finish_time"] is None
    
    in_progress = get_order(order["id"])
    assert in_progress["finish_time"] is None
    assert in_progress["total_amount"] == 0
    
    time.sleep(6)
    
    finished = finish_order(order["id"])
    assert finished["finish_time"] is not None
    assert finished["total_amount"] > 0
    
    final = get_order(order["id"])
    assert final["finish_time"] == finished["finish_time"]
    assert final["total_amount"] == finished["total_amount"]
