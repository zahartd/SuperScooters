import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import jwt
from jwt import InvalidTokenError

from app.models import ConfigMap, OfferData, PricingTokenPayload


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


def generate_pricing_token(
    offer: OfferData,
    user_id: str,
    tariff_version: str,
    pricing_algo_version: str,
    configs: ConfigMap,
) -> str:
    ttl_seconds = int(configs.pricing_token_ttl_seconds)
    secret = str(configs.pricing_token_secret)
    expires_at_dt = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "expires_at": expires_at_dt.isoformat(),
        "tariff_version": tariff_version,
        "pricing_algo_version": pricing_algo_version,
        "offer_hash": _compute_offer_hash(offer),
        "exp": expires_at_dt,
    }

    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        return token.decode("ascii")
    return token


def decode_pricing_token(token: str, configs: ConfigMap) -> PricingTokenPayload:
    secret = str(configs.pricing_token_secret)
    try:
        payload_dict = jwt.decode(token, secret, algorithms=["HS256"])
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


def validate_pricing_token(offer: OfferData, pricing_token: str, configs: ConfigMap) -> PricingTokenPayload:
    payload = decode_pricing_token(pricing_token, configs)

    if payload.user_id != offer.user_id:
        raise ValueError("pricing_token.user_id mismatch")

    if payload.offer_hash != _compute_offer_hash(offer):
        raise ValueError("offer payload was tampered with")

    expires_at = datetime.fromisoformat(payload.expires_at)
    if datetime.now(timezone.utc) > expires_at:
        raise ValueError("pricing_token expired")

    allowed_tariff_version = configs.tariff_version or configs.default_tariff_version
    allowed_algo_version = configs.pricing_algo_version

    if payload.tariff_version != allowed_tariff_version:
        raise ValueError("pricing_token.tariff_version mismatch")

    if payload.pricing_algo_version != allowed_algo_version:
        raise ValueError("pricing_token.pricing_algo_version mismatch")

    return payload
