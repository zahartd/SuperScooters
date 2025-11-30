import pytest

from tests.helpers.api_client import create_offer


@pytest.mark.integration
def test_offer_for_different_zones():
    """Test offers for scooters in different zones"""
    offer1, token1 = create_offer("user-1", "scooter-1")
    offer2, token2 = create_offer("user-1", "zone2-scooter")
    assert offer1["zone_id"]
    assert offer2["zone_id"]
    assert token1
    assert token2


@pytest.mark.integration
def test_same_user_multiple_offers():
    """User should be able to create multiple offers"""
    offers = []
    tokens = []
    
    for i in range(3):
        offer, token = create_offer("user-1", f"scooter-{i+1}")
        offers.append(offer)
        tokens.append(token)
    offer_ids = [o["id"] for o in offers]
    assert len(offer_ids) == len(set(offer_ids))
    assert len(tokens) == len(set(tokens))


@pytest.mark.integration
def test_offer_preserves_scooter_zone():
    """Offer should include the zone where scooter is located"""
    offer, _ = create_offer("user-1", "scooter-1")
    
    assert "zone_id" in offer
    assert offer["zone_id"]
    assert isinstance(offer["zone_id"], str)


@pytest.mark.integration
def test_pricing_consistency_same_params():
    """Creating offer with same params should give same pricing (if no dynamic factors)"""
    offer1, _ = create_offer("user-1", "scooter-1")
    offer2, _ = create_offer("user-1", "scooter-1")
    assert offer1["price_per_minute"] == offer2["price_per_minute"]
    assert offer1["price_unlock"] == offer2["price_unlock"]
    assert offer1["deposit"] == offer2["deposit"]


@pytest.mark.integration
def test_different_scooters_different_zones_different_pricing():
    """Scooters in different zones might have different pricing"""
    offer1, _ = create_offer("user-1", "scooter-1")
    offer2, _ = create_offer("user-1", "zone2-scooter")
    assert offer1["price_per_minute"] > 0
    assert offer2["price_per_minute"] > 0


@pytest.mark.integration
def test_high_debt_user_increased_deposit():
    """User with high debt should have increased deposit"""
    normal_offer, _ = create_offer("user-1", "scooter-1")
    high_debt_offer, _ = create_offer("user-3", "scooter-1")
    assert high_debt_offer["deposit"] > normal_offer["deposit"]
    assert high_debt_offer["deposit"] == int(normal_offer["deposit"] * 1.25)


@pytest.mark.integration
def test_offer_response_structure():
    """Test that offer response has correct structure"""
    offer, token = create_offer("user-1", "scooter-1")
    required_fields = [
        "id", "user_id", "scooter_id", "zone_id",
        "price_per_minute", "price_unlock", "deposit"
    ]
    
    for field in required_fields:
        assert field in offer, f"Missing field: {field}"
        assert offer[field] is not None, f"Null field: {field}"


@pytest.mark.integration
def test_pricing_token_is_unique():
    """Each offer should have a unique pricing token"""
    tokens = []
    
    for i in range(5):
        _, token = create_offer("user-1", f"scooter-{i+1}")
        tokens.append(token)
    assert len(tokens) == len(set(tokens))


@pytest.mark.integration
def test_offer_pricing_values_are_positive():
    """All pricing values should be non-negative"""
    offer, _ = create_offer("user-1", "scooter-1")
    assert offer["price_per_minute"] >= 0
    assert offer["price_unlock"] >= 0
    assert offer["deposit"] >= 0


@pytest.mark.integration
def test_offer_ids_are_strings():
    """All IDs in offer should be strings"""
    offer, token = create_offer("user-1", "scooter-1")
    assert isinstance(offer["id"], str)
    assert isinstance(offer["user_id"], str)
    assert isinstance(offer["scooter_id"], str)
    assert isinstance(offer["zone_id"], str)
    assert isinstance(token, str)


@pytest.mark.integration
def test_multiple_users_same_scooter_offers():
    """Multiple users should be able to get offers for the same scooter"""
    offer1, _ = create_offer("user-1", "scooter-1")
    offer2, _ = create_offer("user-4", "scooter-1")
    assert offer1["scooter_id"] == "scooter-1"
    assert offer2["scooter_id"] == "scooter-1"
    assert offer1["id"] != offer2["id"]
