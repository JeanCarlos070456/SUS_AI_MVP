from __future__ import annotations
import time
import requests
from dataclasses import dataclass
from typing import Iterable, Optional

@dataclass
class HttpConfig:
    timeout_connect: float = 5.0
    timeout_read: float = 25.0
    max_retries: int = 3
    backoff_base: float = 0.6
    retry_statuses: tuple[int, ...] = (429, 500, 502, 503, 504)

def make_session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": "sus-ai-mvp/1.0"})
    return s

def request_json(
    session: requests.Session,
    method: str,
    url: str,
    *,
    params: dict | None = None,
    headers: dict | None = None,
    config: HttpConfig | None = None,
) -> dict:
    cfg = config or HttpConfig()
    last_err: Exception | None = None
    for attempt in range(cfg.max_retries):
        try:
            r = session.request(
                method=method.upper(),
                url=url,
                params=params,
                headers=headers,
                timeout=(cfg.timeout_connect, cfg.timeout_read),
            )
            if r.status_code in cfg.retry_statuses:
                raise requests.HTTPError(f"HTTP {r.status_code}: {r.text[:200]}", response=r)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last_err = e
            # backoff
            time.sleep(cfg.backoff_base * (2 ** attempt))
    raise last_err  # type: ignore[misc]
