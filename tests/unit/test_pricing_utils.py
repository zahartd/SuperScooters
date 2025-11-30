import pytest
from datetime import datetime, timedelta
from app.models import OfferData
from app.utils.pricing import (
    generate_pricing_token,
    decode_pricing_token,
    validate_pricing_token,
    _compute_offer_hash,
    _canonical_offer_json,
)


@pytest.fixture
def sample_offer():
    return OfferData(
        id="offer-123",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )


@pytest.fixture
def sample_configs():
    class Config:
        tariff_version = "v1"
        pricing_algo_version = "v1"
    return Config()


def test_canonical_offer_json_is_deterministic(sample_offer):
    """Test that canonical JSON is always the same for same offer"""
    json1 = _canonical_offer_json(sample_offer)
    json2 = _canonical_offer_json(sample_offer)
    
    assert json1 == json2


def test_canonical_offer_json_is_sorted(sample_offer):
    """Test that canonical JSON has sorted keys"""
    json_str = _canonical_offer_json(sample_offer)
    
    assert "deposit" in json_str
    assert json_str.index("deposit") < json_str.index("id")
    assert json_str.index("id") < json_str.index("price_per_minute")


def test_compute_offer_hash_is_deterministic(sample_offer):
    """Test that offer hash is always the same for same offer"""
    hash1 = _compute_offer_hash(sample_offer)
    hash2 = _compute_offer_hash(sample_offer)
    
    assert hash1 == hash2
    assert isinstance(hash1, str)
    assert len(hash1) == 64


def test_compute_offer_hash_changes_with_offer():
    """Test that different offers produce different hashes"""
    offer1 = OfferData(
        id="offer-1",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )
    
    offer2 = OfferData(
        id="offer-2",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )
    
    hash1 = _compute_offer_hash(offer1)
    hash2 = _compute_offer_hash(offer2)
    
    assert hash1 != hash2


def test_generate_pricing_token_creates_valid_token(sample_offer):
    """Test that generated token can be decoded"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id="user-1",
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    payload = decode_pricing_token(token)
    assert payload.user_id == "user-1"


def test_decode_pricing_token_returns_payload(sample_offer):
    """Test that decoded token contains expected fields"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id="user-1",
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    payload = decode_pricing_token(token)
    
    assert payload.user_id == "user-1"
    assert payload.tariff_version == "v1"
    assert payload.pricing_algo_version == "v1"
    assert payload.offer_hash
    assert payload.expires_at


def test_decode_pricing_token_raises_on_invalid():
    """Test that invalid token raises ValueError"""
    with pytest.raises(ValueError, match="invalid or expired"):
        decode_pricing_token("invalid-token")


def test_decode_pricing_token_raises_on_empty():
    """Test that empty token raises ValueError"""
    with pytest.raises(ValueError):
        decode_pricing_token("")


def test_validate_pricing_token_accepts_valid_token(sample_offer, sample_configs):
    """Test that valid token passes validation"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id=sample_offer.user_id,
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    payload = validate_pricing_token(sample_offer, token, sample_configs)
    assert payload.user_id == sample_offer.user_id


def test_validate_pricing_token_rejects_wrong_user(sample_offer, sample_configs):
    """Test that token for different user is rejected"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id="different-user",
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    with pytest.raises(ValueError, match="user_id mismatch"):
        validate_pricing_token(sample_offer, token, sample_configs)


def test_validate_pricing_token_rejects_tampered_offer(sample_configs):
    """Test that tampered offer is rejected"""
    original_offer = OfferData(
        id="offer-123",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )
    
    token = generate_pricing_token(
        offer=original_offer,
        user_id="user-1",
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    tampered_offer = OfferData(
        id="offer-123",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=1,
        price_unlock=100,
        deposit=300,
    )
    
    with pytest.raises(ValueError, match="tampered"):
        validate_pricing_token(tampered_offer, token, sample_configs)


def test_validate_pricing_token_rejects_wrong_tariff_version(sample_offer):
    """Test that token with wrong tariff version is rejected"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id=sample_offer.user_id,
        tariff_version="v2",
        pricing_algo_version="v1",
    )
    
    class Config:
        tariff_version = "v1"
        pricing_algo_version = "v1"
    
    with pytest.raises(ValueError, match="tariff_version mismatch"):
        validate_pricing_token(sample_offer, token, Config())


def test_validate_pricing_token_rejects_wrong_algo_version(sample_offer):
    """Test that token with wrong algo version is rejected"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id=sample_offer.user_id,
        tariff_version="v1",
        pricing_algo_version="v2",
    )
    
    class Config:
        tariff_version = "v1"
        pricing_algo_version = "v1"
    
    with pytest.raises(ValueError, match="pricing_algo_version mismatch"):
        validate_pricing_token(sample_offer, token, Config())


def test_pricing_token_has_expiration(sample_offer):
    """Test that pricing token includes expiration"""
    token = generate_pricing_token(
        offer=sample_offer,
        user_id="user-1",
        tariff_version="v1",
        pricing_algo_version="v1",
    )
    
    payload = decode_pricing_token(token)
    expires_at = datetime.fromisoformat(payload.expires_at)
    
    assert expires_at > datetime.utcnow()
    assert expires_at < datetime.utcnow() + timedelta(minutes=5)


def test_different_offers_produce_different_tokens():
    """Test that different offers produce different tokens"""
    offer1 = OfferData(
        id="offer-1",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )
    
    offer2 = OfferData(
        id="offer-2",
        user_id="user-1",
        scooter_id="scooter-1",
        zone_id="zone-1",
        price_per_minute=5,
        price_unlock=100,
        deposit=300,
    )
    
    token1 = generate_pricing_token(offer1, "user-1", "v1", "v1")
    token2 = generate_pricing_token(offer2, "user-1", "v1", "v1")
    
    assert token1 != token2
