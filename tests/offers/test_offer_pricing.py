import pytest

from tests.helpers.api_client import create_offer

@pytest.mark.integration
def test_offer_with_surge_pricing():
    """Test that surge pricing affects price per minute"""
    offer, token = create_offer("user-1", "surge-zone-scooter")
    
    assert offer["price_per_minute"] > 0
    assert token


@pytest.mark.integration
def test_offer_deposit_calculation_high_debt():
    """Users with high total debt should have 1.25x deposit"""
    offer, _ = create_offer("user-3", "scooter-1")
    
    assert offer["deposit"] > 0
    assert offer["deposit"] == 375


@pytest.mark.integration
def test_offer_deposit_calculation_normal_user():
    """Normal users should have standard deposit"""
    offer, _ = create_offer("user-1", "scooter-1")
    
    assert offer["deposit"] == 300


@pytest.mark.integration
def test_offer_includes_zone_id():
    """Offer should include zone_id from scooter location"""
    offer, token = create_offer("user-1", "scooter-1")
    
    assert "zone_id" in offer
    assert offer["zone_id"]


@pytest.mark.integration
def test_offer_has_unique_id():
    """Each offer should have a unique ID"""
    offer1, _ = create_offer("user-1", "scooter-1")
    offer2, _ = create_offer("user-1", "scooter-2")
    
    assert offer1["id"] != offer2["id"]


@pytest.mark.integration
def test_multiple_offers_same_scooter():
    """Should be able to create multiple offers for same scooter"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    offer2, token2 = create_offer("user-4", "scooter-1")
    
    assert offer1["scooter_id"] == offer2["scooter_id"]
    assert offer1["id"] != offer2["id"]
    assert token1 != token2
