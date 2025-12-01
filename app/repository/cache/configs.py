import structlog

from typing import Optional

from app.clients import data_requests as dr
from app.models import ConfigMap
from app.static_config import static_config


logger = structlog.get_logger(__name__)


def get_configs(base_config: Optional[ConfigMap] = None) -> ConfigMap:
    merged = (base_config or static_config).clone()
    try:
        dynamic = dr.get_configs()
        merged.merge(dynamic)
        logger.debug("configs: fetched dynamic configs")
    except Exception as exc:
        logger.warning(
            "configs: failed to fetch dynamic configs, using fallback",
            error=str(exc),
        )

    return merged


class ConfigProvider:
    def __init__(self, base_config: Optional[ConfigMap] = None):
        self._config = get_configs(base_config)

    @property
    def data(self) -> ConfigMap:
        return self._config

    def get(self, *path, default=None):
        return self._config.get_path(*path, default=default)
