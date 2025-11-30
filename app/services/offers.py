import uuid

from app.clients import data_requests as dr
from app.models import OfferData
from app.utils.pricing import DEFAULT_TARIFF_VERSION, PRICING_ALGO_VERSION, generate_pricing_token

MAGIC_CONSTANT = 28


def create_offer(scooter_id: str, user_id: str):
    scooter_data = dr.get_scooter_data(scooter_id)
    tariff = dr.get_tariff_zone(scooter_data.zone_id)
    user_profile = dr.get_user_profile(user_id)
    configs = dr.get_configs()

    actual_price_per_min = tariff.price_per_minute
    if configs.price_coeff_settings is not None:
        actual_price_per_min = int(actual_price_per_min * float(configs.price_coeff_settings["surge"]))
        if scooter_data.charge < MAGIC_CONSTANT:
            actual_price_per_min = int(
                actual_price_per_min * float(configs.price_coeff_settings["low_charge_discount"])
            )

    actual_price_unlock = 0 if user_profile.has_subscribtion else tariff.price_unlock

    offer = OfferData(
        str(uuid.uuid4()),
        user_id=user_id,
        scooter_id=scooter_id,
        zone_id=scooter_data.zone_id,
        price_per_minute=actual_price_per_min,
        price_unlock=actual_price_unlock,
        deposit=0 if user_profile.trusted else tariff.default_deposit,
    )

    tariff_version = getattr(configs, "tariff_version", DEFAULT_TARIFF_VERSION) or DEFAULT_TARIFF_VERSION
    pricing_token = generate_pricing_token(
        offer=offer,
        user_id=user_id,
        tariff_version=tariff_version,
        pricing_algo_version=PRICING_ALGO_VERSION,
    )

    return offer, pricing_token
