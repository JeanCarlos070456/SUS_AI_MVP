from __future__ import annotations
import json
from dataclasses import dataclass
from pathlib import Path
from core.utils import tokenize, now_iso
from core.errors import IndexError

@dataclass
class Chunk:
    chunk_id: str
    doc_id: str
    name: str
    text: str
    offset: int

def chunk_text(text: str, *, max_tokens: int = 180, overlap: int = 40) -> list[str]:
    toks = tokenize(text)
    if not toks:
        return []
    chunks = []
    i = 0
    while i < len(toks):
        part = toks[i:i+max_tokens]
        chunks.append(" ".join(part))
        i += max(1, max_tokens - overlap)
    return chunks

def build_index(docs: list[dict], out_path: str):
    # docs: [{doc_id,name,text}]
    inv: dict[str, list[str]] = {}
    chunks_meta: dict[str, dict] = {}
    for d in docs:
        pieces = chunk_text(d.get("text",""))
        for j, piece in enumerate(pieces):
            cid = f"{d['doc_id']}::c{j}"
            chunks_meta[cid] = {
                "doc_id": d["doc_id"],
                "name": d.get("name", d["doc_id"]),
                "text": piece,
                "offset": j,
            }
            for t in set(piece.split()):
                inv.setdefault(t, []).append(cid)

    payload = {
        "version": 1,
        "built_at": now_iso(),
        "chunk_count": len(chunks_meta),
        "inv": inv,
        "chunks": chunks_meta,
    }
    p = Path(out_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

def search(index_path: str, query: str, *, top_k: int = 5) -> list[dict]:
    p = Path(index_path)
    if not p.exists():
        raise IndexError(f"Índice não encontrado: {index_path}")
    idx = json.loads(p.read_text(encoding="utf-8"))
    inv = idx.get("inv", {})
    chunks = idx.get("chunks", {})
    q = tokenize(query)
    if not q:
        return []
    scores: dict[str, int] = {}
    for t in set(q):
        for cid in inv.get(t, []):
            scores[cid] = scores.get(cid, 0) + 1
    best = sorted(scores.items(), key=lambda x: (-x[1], x[0]))[:top_k]
    out = []
    for cid, sc in best:
        ch = chunks.get(cid)
        if ch:
            out.append({"score": sc, "chunk_id": cid, **ch})
    return out
