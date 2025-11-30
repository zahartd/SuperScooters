import pytest
import requests
import os

API_URL = os.getenv("API_URL", "http://api:8000")


@pytest.mark.integration
def test_create_offer_missing_user_id():
    """Creating offer without user_id should fail"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={"scooter_id": "scooter-1"},
        timeout=5,
    )
    assert resp.status_code == 422  # Validation error


@pytest.mark.integration
def test_create_offer_missing_scooter_id():
    """Creating offer without scooter_id should fail"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-1"},
        timeout=5,
    )
    assert resp.status_code == 422  # Validation error


@pytest.mark.integration
def test_create_offer_empty_payload():
    """Creating offer with empty payload should fail"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={},
        timeout=5,
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_create_offer_invalid_json():
    """Creating offer with invalid JSON should fail"""
    resp = requests.post(
        f"{API_URL}/offers",
        data="not json",
        headers={"Content-Type": "application/json"},
        timeout=5,
    )
    assert resp.status_code == 422


@pytest.mark.integration
def test_create_offer_user_with_active_debt():
    """Users with current debt should not be able to create offers"""
    resp = requests.post(
        f"{API_URL}/offers",
        json={"user_id": "user-2", "scooter_id": "scooter-1"},
        timeout=5,
    )
    
    # Should succeed but return error in response
    assert resp.status_code == 200
    data = resp.json()
    assert data["error"] is not None
    assert "debt" in data["error"].lower()
    assert data["offer"] is None
    assert data["pricing_token"] is None

