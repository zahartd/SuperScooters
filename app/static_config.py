from app.models import ConfigMap

static_config = ConfigMap({
    "price_coeff_settings": {
        "surge": 2.5,
        "low_charge_discount": 0.5,
        "low_charge_threshold": 28,
    },
    "pricing_rules": {
        "deposit_multiplier": 1.25,
        "deposit_debt_threshold": 10_000,
        "free_ride_seconds_threshold": 5,
    },
    "cache_settings": {
        "orders_ttl_seconds": 2 * 60 * 60,
        "orders_maxsize": 150_000,
        "zones_ttl_seconds": 600,
        "zones_maxsize": 10_000,
        "configs_ttl_seconds": 60,
        "configs_maxsize": 4,
    },
    "external_services": {
        "base_url": "http://localhost:3629",
    },
    "pricing_token_secret": "super-secret-pricing-key",
    "pricing_token_ttl_seconds": 180,
    "pricing_algo_version": "v1",
    "default_tariff_version": "v1",
})
