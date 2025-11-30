import structlog

from app.clients import data_requests as dr
from app.models import TariffZone
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

# ADR: zones are read-only, cached with LRU + TTL ~10 minutes.
_ZONE_CACHE_TTL_SECONDS = 600
_ZONE_CACHE_MAXSIZE = 10_000

_zone_cache: ThreadSafeTTLCache[str, TariffZone] = ThreadSafeTTLCache(
    maxsize=_ZONE_CACHE_MAXSIZE,
    ttl=_ZONE_CACHE_TTL_SECONDS,
)


def get_tariff_zone(zone_id: str) -> TariffZone:
    cached = _zone_cache.get(zone_id)
    if cached is not None:
        logger.debug("zones_repo: cache hit", zone_id=zone_id)
        return cached

    tariff_zone = dr.get_tariff_zone(zone_id)
    _zone_cache.set(zone_id, tariff_zone)
    logger.debug("zones_repo: cache stored", zone_id=zone_id)
    return tariff_zone
