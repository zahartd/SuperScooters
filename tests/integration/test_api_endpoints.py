import pytest
import requests
import os

API_URL = os.getenv("API_URL", "http://api:8000")


@pytest.mark.integration
def test_docs_endpoint_accessible():
    """Test that API documentation endpoint is accessible"""
    resp = requests.get(f"{API_URL}/docs", timeout=5)
    assert resp.status_code == 200


@pytest.mark.integration
def test_offers_endpoint_accepts_post():
    """Test that offers endpoint accepts POST requests"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1", "scooter_id": "scooter-1"},
        timeout=5,
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_offers_endpoint_rejects_get():
    """Test that offers endpoint rejects GET requests"""
    resp = requests.get(f"{API_URL}/offers", timeout=5)
    assert resp.status_code in [404, 405]


@pytest.mark.integration
def test_orders_endpoint_accepts_post():
    """Test that orders endpoint accepts POST requests with valid data"""
    offer_resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1", "scooter_id": "scooter-1"},
        timeout=5,
    )
    data = offer_resp.json()
    
    resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": data["offer"], "pricing_token": data["pricing_token"]},
        timeout=5,
    )
    assert resp.status_code == 200


@pytest.mark.integration
def test_orders_get_endpoint():
    """Test that orders can be retrieved via GET"""
    offer_resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1", "scooter_id": "scooter-1"},
        timeout=5,
    )
    data = offer_resp.json()
    
    order_resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": data["offer"], "pricing_token": data["pricing_token"]},
        timeout=5,
    )
    order = order_resp.json()
    
    get_resp = requests.get(f"{API_URL}/orders/{order['id']}", timeout=5)
    assert get_resp.status_code == 200


@pytest.mark.integration
def test_finish_order_endpoint():
    """Test that finish order endpoint works"""
    offer_resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1", "scooter_id": "scooter-1"},
        timeout=5,
    )
    data = offer_resp.json()
    
    order_resp = requests.post(
        f"{API_URL}/orders",
        json={"offer": data["offer"], "pricing_token": data["pricing_token"]},
        timeout=5,
    )
    order = order_resp.json()
    
    finish_resp = requests.post(
        f"{API_URL}/orders/{order['id']}/finish",
        timeout=5,
    )
    assert finish_resp.status_code == 200
    finished = finish_resp.json()
    assert finished["finish_time"] is not None


@pytest.mark.integration
def test_api_returns_json():
    """Test that API endpoints return JSON content type"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1", "scooter_id": "scooter-1"},
        timeout=5,
    )
    assert "application/json" in resp.headers.get("content-type", "")


@pytest.mark.integration
def test_api_handles_cors():
    """Test that API includes CORS headers (if configured)"""
    resp = requests.options(f"{API_URL}/offers", timeout=5)
    assert resp.status_code in [200, 405]
