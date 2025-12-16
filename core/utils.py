from __future__ import annotations
import re
from datetime import datetime
from typing import Iterable

_token_re = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9]+", re.UNICODE)

def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _token_re.findall(text or "") if len(t) >= 2]

def now_iso() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def uniq(seq: Iterable):
    seen = set()
    out = []
    for x in seq:
        if x not in seen:
            out.append(x)
            seen.add(x)
    return out
