import os
import time
from typing import Iterator

import pytest
import requests

API_URL = os.getenv("API_URL", "http://api:8000")


@pytest.fixture(scope="session", autouse=True)
def wait_for_api() -> Iterator[str]:
    deadline = time.time() + 60
    while time.time() < deadline:
        try:
            resp = requests.get(f"{API_URL}/docs", timeout=2)
            if resp.status_code < 500:
                break
        except requests.RequestException:
            pass
        time.sleep(1)
    else:
        raise RuntimeError("API not reachable within timeout")
    yield API_URL
