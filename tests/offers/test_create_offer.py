import pytest

from tests.helpers.api_client import create_offer


@pytest.mark.integration
def test_create_offer_returns_pricing_token():
    offer, token = create_offer("user-1", "scooter-1")

    assert offer["user_id"] == "user-1"
    assert offer["scooter_id"] == "scooter-1"
    assert token
    assert isinstance(token, str)
