import uuid
import structlog

from app.clients import data_requests as dr
from app.models import ConfigMap, OfferData, TariffZone, UserProfile
from app.repository.cache import configs as configs_repo
from app.repository.cache import zones as zones_repo
from app.utils.pricing import DEFAULT_TARIFF_VERSION, PRICING_ALGO_VERSION, generate_pricing_token

logger = structlog.get_logger(__name__)


class CreateOfferError:
    def __init__(self, message: str):
        self.message = message


def create_offer(scooter_id: str, user_id: str, configs: ConfigMap) -> tuple[OfferData, str] | CreateOfferError:
    logger.info("create_offer: start", scooter_id=scooter_id, user_id=user_id)

    scooter_data = dr.get_scooter_data(scooter_id)
    tariff = zones_repo.get_tariff_zone(scooter_data.zone_id)
    user_profile = dr.get_user_profile(user_id)

    configs = configs_repo.get_configs(configs)

    if user_profile.current_debt > 0:
        logger.warning(
            "create_offer: user has debt", user_id=user_id, current_debt=user_profile.current_debt
        )
        return CreateOfferError("User has debt")

    actual_price_per_min = tariff.price_per_minute
    if configs.price_coeff_settings is not None:
        actual_price_per_min = int(actual_price_per_min * float(configs.price_coeff_settings["surge"]))
        low_charge_threshold = float(configs.price_coeff_settings.get("low_charge_threshold", 28))
        if scooter_data.charge < low_charge_threshold:
            actual_price_per_min = int(
                actual_price_per_min * float(configs.price_coeff_settings["low_charge_discount"])
            )

    logger.debug(
        "create_offer: pricing calculated",
        user_id=user_id,
        scooter_id=scooter_id,
        price_per_min=actual_price_per_min,
        price_unlock=tariff.price_unlock,
        deposit_default=tariff.default_deposit,
    )

    actual_price_unlock = 0 if user_profile.has_subscribtion else tariff.price_unlock

    def calc_deposit(user_profile: UserProfile, tariff: TariffZone) -> int:
        rules = getattr(configs, "pricing_rules", {}) or {}
        deposit_multiplier = float(rules.get("deposit_multiplier", 1.25))
        deposit_debt_threshold = int(rules.get("deposit_debt_threshold", 10_000))
        if user_profile.trusted:
            return 0
        multiplier = deposit_multiplier if user_profile.total_debt > deposit_debt_threshold else 1.0
        return int(tariff.default_deposit * multiplier)

    offer = OfferData(
        str(uuid.uuid4()),
        user_id=user_id,
        scooter_id=scooter_id,
        zone_id=scooter_data.zone_id,
        price_per_minute=actual_price_per_min,
        price_unlock=actual_price_unlock,
        deposit=calc_deposit(user_profile, tariff),
    )

    tariff_version = getattr(configs, "tariff_version", DEFAULT_TARIFF_VERSION) or DEFAULT_TARIFF_VERSION
    pricing_token = generate_pricing_token(
        offer=offer,
        user_id=user_id,
        tariff_version=tariff_version,
        pricing_algo_version=PRICING_ALGO_VERSION,
    )

    logger.info(
        "create_offer: success",
        offer_id=offer.id,
        user_id=user_id,
        scooter_id=scooter_id,
        zone_id=scooter_data.zone_id,
    )

    return offer, pricing_token
