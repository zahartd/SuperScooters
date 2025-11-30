import hashlib
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from jwt import InvalidTokenError

from app.models import OfferData, PricingTokenPayload

# Defaults kept local; in production should be configurable via env/config provider.
PRICING_TOKEN_TTL_SECONDS = 180
PRICING_TOKEN_SECRET = "super-secret-pricing-key"
PRICING_ALGO_VERSION = "v1"
DEFAULT_TARIFF_VERSION = "v1"
logger = logging.getLogger(__name__)


def _canonical_offer_json(offer: OfferData) -> str:
    payload = {
        "deposit": offer.deposit,
        "id": offer.id,
        "price_per_minute": offer.price_per_minute,
        "price_unlock": offer.price_unlock,
        "scooter_id": offer.scooter_id,
        "user_id": offer.user_id,
        "zone_id": offer.zone_id,
    }
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def _compute_offer_hash(offer: OfferData) -> str:
    canonical = _canonical_offer_json(offer)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def generate_pricing_token(offer: OfferData, user_id: str, tariff_version: str, pricing_algo_version: str) -> str:
    expires_at_dt = datetime.utcnow() + timedelta(seconds=PRICING_TOKEN_TTL_SECONDS)
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "expires_at": expires_at_dt.isoformat(),
        "tariff_version": tariff_version,
        "pricing_algo_version": pricing_algo_version,
        "offer_hash": _compute_offer_hash(offer),
        "exp": expires_at_dt,
    }

    token = jwt.encode(payload, PRICING_TOKEN_SECRET, algorithm="HS256")
    logger.debug(
        "pricing: generated token offer_id=%s user_id=%s tariff_version=%s pricing_algo_version=%s",
        offer.id,
        user_id,
        tariff_version,
        pricing_algo_version,
    )
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def decode_pricing_token(token: str) -> PricingTokenPayload:
    try:
        payload_dict = jwt.decode(token, PRICING_TOKEN_SECRET, algorithms=["HS256"])
    except InvalidTokenError as exc:
        logger.warning("pricing: token decode failed")
        raise ValueError("pricing_token is invalid or expired") from exc

    required = {"user_id", "expires_at", "tariff_version", "pricing_algo_version", "offer_hash"}
    if not required.issubset(payload_dict):
        raise ValueError("pricing_token is missing required fields")

    return PricingTokenPayload(
        user_id=str(payload_dict["user_id"]),
        expires_at=str(payload_dict["expires_at"]),
        tariff_version=str(payload_dict["tariff_version"]),
        pricing_algo_version=str(payload_dict["pricing_algo_version"]),
        offer_hash=str(payload_dict["offer_hash"]),
    )


def validate_pricing_token(offer: OfferData, pricing_token: str, configs) -> PricingTokenPayload:
    payload = decode_pricing_token(pricing_token)

    if payload.user_id != offer.user_id:
        logger.warning(
            "pricing: user_id mismatch offer_user_id=%s token_user_id=%s", offer.user_id, payload.user_id
        )
        raise ValueError("pricing_token.user_id mismatch")

    if payload.offer_hash != _compute_offer_hash(offer):
        logger.warning("pricing: offer hash mismatch offer_id=%s", offer.id)
        raise ValueError("offer payload was tampered with")

    expires_at = datetime.fromisoformat(payload.expires_at)
    if datetime.utcnow() > expires_at:
        logger.warning("pricing: token expired offer_id=%s user_id=%s", offer.id, offer.user_id)
        raise ValueError("pricing_token expired")

    allowed_tariff_version = getattr(configs, "tariff_version", DEFAULT_TARIFF_VERSION) or DEFAULT_TARIFF_VERSION
    allowed_algo_version = getattr(configs, "pricing_algo_version", PRICING_ALGO_VERSION) or PRICING_ALGO_VERSION

    if payload.tariff_version != allowed_tariff_version:
        logger.warning(
            "pricing: tariff version mismatch offer_id=%s expected=%s got=%s",
            offer.id,
            allowed_tariff_version,
            payload.tariff_version,
        )
        raise ValueError("pricing_token.tariff_version mismatch")

    if payload.pricing_algo_version != allowed_algo_version:
        logger.warning(
            "pricing: algo version mismatch offer_id=%s expected=%s got=%s",
            offer.id,
            allowed_algo_version,
            payload.pricing_algo_version,
        )
        raise ValueError("pricing_token.pricing_algo_version mismatch")

    logger.debug("pricing: token validated offer_id=%s user_id=%s", offer.id, offer.user_id)
    return payload
