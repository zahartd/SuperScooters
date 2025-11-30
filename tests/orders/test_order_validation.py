import pytest
import requests
import os

from tests.helpers.api_client import create_offer, start_order

API_URL = os.getenv("API_URL", "http://api:8000")


@pytest.mark.integration
def test_start_order_with_invalid_token():
    """Starting order with invalid pricing token should fail"""
    offer, _ = create_offer("user-1", "scooter-1")
    
    resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": offer, "pricing_token": "invalid-token"},
        timeout=5,
    )
    assert resp.status_code == 400


@pytest.mark.integration
def test_start_order_missing_token():
    """Starting order without pricing token should fail"""
    offer, _ = create_offer("user-1", "scooter-1")
    
    resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": offer},
        timeout=5,
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_start_order_missing_offer():
    """Starting order without offer should fail"""
    _, token = create_offer("user-1", "scooter-1")
    
    resp = requests.post(
        f"{API_URL}/orders",
        json={"pricing_token": token},
        timeout=5,
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_order_has_all_required_fields():
    """Order response should contain all required fields"""
    offer, token = create_offer("user-1", "scooter-1")
    order = start_order(offer, token)
    
    required_fields = [
        "id", "user_id", "scooter_id", "zone_id",
        "price_per_minute", "price_unlock", "deposit",
        "total_amount", "start_time"
    ]
    
    for field in required_fields:
        assert field in order
        assert order[field] is not None or field == "finish_time"

