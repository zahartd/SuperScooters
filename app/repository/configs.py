import structlog

from app.clients import data_requests as dr
from app.models import ConfigMap
from app.static_config import static_config
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

# ADR: configs are small and refreshed up to once a minute with a static fallback.
_CONFIG_CACHE_TTL_SECONDS = 60
_CONFIG_CACHE_MAXSIZE = 4
_CONFIG_CACHE_KEY = "config"

_config_cache: ThreadSafeTTLCache[str, ConfigMap] = ThreadSafeTTLCache(
    maxsize=_CONFIG_CACHE_MAXSIZE,
    ttl=_CONFIG_CACHE_TTL_SECONDS,
)


def _cache_config(config: ConfigMap) -> None:
    _config_cache.set(_CONFIG_CACHE_KEY, config.clone())


def _cached_config() -> ConfigMap | None:
    cached = _config_cache.get(_CONFIG_CACHE_KEY)
    return cached.clone() if cached is not None else None


def get_configs(base_config: ConfigMap | None = None) -> ConfigMap:
    """
    Returns a merged config map with dynamic values, cached with TTL.
    Falls back to the last good value or static config when external fetch fails.
    """
    cached = _cached_config()
    if cached:
        logger.debug("configs_repo: cache hit")
        return cached

    merged = (base_config or static_config).clone()
    try:
        dynamic = dr.get_configs()
        merged.merge(dynamic)
        logger.debug("configs_repo: fetched and merged dynamic configs")
    except Exception as exc:  # noqa: BLE001
        logger.warning(
            "configs_repo: failed to fetch dynamic configs, using fallback",
            error=str(exc),
        )
        if cached:
            return cached

    _cache_config(merged)
    return merged
