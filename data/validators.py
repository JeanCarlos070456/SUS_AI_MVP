from __future__ import annotations

def require_cols(df, cols: list[str], where: str = ""):
    missing = [c for c in cols if c not in df.columns]
    if missing:
        loc = f" em {where}" if where else ""
        raise ValueError(f"Colunas ausentes{loc}: {missing}")
