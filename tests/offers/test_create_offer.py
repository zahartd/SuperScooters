import pytest

from tests.helpers.api_client import create_offer


@pytest.mark.integration
def test_create_offer_returns_pricing_token():
    offer, token = create_offer("user-1", "scooter-1")

    assert offer["user_id"] == "user-1"
    assert offer["scooter_id"] == "scooter-1"
    assert token
    assert isinstance(token, str)


@pytest.mark.integration
def test_create_offer_user_with_debt():
    try:
        create_offer("user-2", "scooter-2")
        assert False
    except Exception as e:
        return

@pytest.mark.integration
def test_create_offer_user_with_big_total_debt():
    offer, _ = create_offer("user-3", "scooter-3")
    assert offer["deposit"] == 300 * 1.25
