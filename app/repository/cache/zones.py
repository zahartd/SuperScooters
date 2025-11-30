import structlog

from app.clients import data_requests as dr
from app.models import TariffZone
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

_ZONE_CACHE_TTL_SECONDS = 600  # ADR: zones cached for ~10 minutes
_ZONE_CACHE_MAXSIZE = 10_000

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
