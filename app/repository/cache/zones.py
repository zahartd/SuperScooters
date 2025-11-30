import structlog

from app.clients import data_requests as dr
from app.models import TariffZone
from app.static_config import static_config
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

_cache_settings = getattr(static_config, "cache_settings", {}) or {}
_ZONE_CACHE_TTL_SECONDS = int(_cache_settings.get("zones_ttl_seconds", 600))
_ZONE_CACHE_MAXSIZE = int(_cache_settings.get("zones_maxsize", 10_000))

_zone_cache: ThreadSafeTTLCache[str, TariffZone] = ThreadSafeTTLCache(
    maxsize=_ZONE_CACHE_MAXSIZE,
    ttl=_ZONE_CACHE_TTL_SECONDS,
)


def get_tariff_zone(zone_id: str) -> TariffZone:
    cached = _zone_cache.get(zone_id)
    if cached is not None:
        logger.debug("zones_cache: cache hit", zone_id=zone_id)
        return cached

    tariff_zone = dr.get_tariff_zone(zone_id)
    _zone_cache.set(zone_id, tariff_zone)
    logger.debug("zones_cache: cached zone", zone_id=zone_id)
    return tariff_zone
