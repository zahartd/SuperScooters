import structlog

from app.clients import data_requests as dr
from app.models import ConfigMap
from app.static_config import static_config
from app.utils.cache import ThreadSafeTTLCache


logger = structlog.get_logger(__name__)

_cache_settings = getattr(static_config, "cache_settings", {}) or {}
_CONFIG_CACHE_TTL_SECONDS = int(_cache_settings.get("configs_ttl_seconds", 60))
_CONFIG_CACHE_MAXSIZE = int(_cache_settings.get("configs_maxsize", 4))
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
    Returns merged static+dynamic configs with TTL cache and fallback to last good value.
    """
    cached = _cached_config()
    if cached:
        logger.debug("configs_cache: cache hit")
        return cached

    merged = (base_config or static_config).clone()
    try:
        dynamic = dr.get_configs()
        merged.merge(dynamic)
        logger.debug("configs_cache: fetched dynamic configs")
    except Exception as exc:
        logger.warning(
            "configs_cache: failed to fetch dynamic configs, using fallback",
            error=str(exc),
        )
        if cached:
            return cached

    _cache_config(merged)
    return merged
