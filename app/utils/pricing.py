import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Dict

import jwt
from jwt import InvalidTokenError

from app.models import OfferData, PricingTokenPayload

PRICING_TOKEN_TTL_SECONDS = 180
PRICING_TOKEN_SECRET = "super-secret-pricing-key"
PRICING_ALGO_VERSION = "v1"
DEFAULT_TARIFF_VERSION = "v1"


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
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def decode_pricing_token(token: str) -> PricingTokenPayload:
    try:
        payload_dict = jwt.decode(token, PRICING_TOKEN_SECRET, algorithms=["HS256"])
    except InvalidTokenError as exc:
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
        raise ValueError("pricing_token.user_id mismatch")

    if payload.offer_hash != _compute_offer_hash(offer):
        raise ValueError("offer payload was tampered with")

    expires_at = datetime.fromisoformat(payload.expires_at)
    if datetime.utcnow() > expires_at:
        raise ValueError("pricing_token expired")

    allowed_tariff_version = getattr(configs, "tariff_version", DEFAULT_TARIFF_VERSION) or DEFAULT_TARIFF_VERSION
    allowed_algo_version = getattr(configs, "pricing_algo_version", PRICING_ALGO_VERSION) or PRICING_ALGO_VERSION

    if payload.tariff_version != allowed_tariff_version:
        raise ValueError("pricing_token.tariff_version mismatch")

    if payload.pricing_algo_version != allowed_algo_version:
        raise ValueError("pricing_token.pricing_algo_version mismatch")

    return payload
