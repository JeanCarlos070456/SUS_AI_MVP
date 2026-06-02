from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_CATALOG_JSON = PROJECT_ROOT / "scripts" / "drive_catalog.json"
DEFAULT_CATALOG_SUMMARY_JSON = PROJECT_ROOT / "scripts" / "drive_catalog_summary.json"


INSTITUTIONAL_KEYWORDS = {
    # Núcleo MAIC
    "maic",
    "monitoramento",
    "avaliacao",
    "avaliação",
    "indicador",
    "indicadores",
    "custo",
    "custos",
    "gestao",
    "gestão",

    # Áreas internas
    "gemag",
    "gemap",
    "gemac",
    "dimoas",
    "suplans",
    "cplan",

    # Bases e instrumentos
    "imd",
    "rgqc",
    "apura",
    "apurasus",
    "apura sus",
    "producao",
    "produção",
    "acordo",
    "acordos",
    "pds",
    "pas",
    "rdqa",
    "catalogo",
    "catálogo",

    # Recortes institucionais
    "regiao",
    "região",
    "regional",
    "srs",
    "unidade",
    "unidades",
    "hospital",
    "hospitais",
    "policlinica",
    "policlínica",
    "ubs",
    "upa",
    "caps",
    "samu",
}


AREA_ALIASES = {
    "custos": "CUSTOS",
    "custo": "CUSTOS",
    "gemac": "GEMAC",
    "gemag": "GEMAG",
    "gemap": "GEMAP",
    "pdf": "PDF",
    "docs": "DOCS",
    "documentos": "DOCS",
    "sheets": "SHEETS",
    "planilhas": "SHEETS",
    "exports": "EXPORTS",
    "export": "EXPORTS",
}


CATEGORY_ALIASES = {
    "pdf": "documento_pdf",
    "documento": "documento_pdf",
    "documentos": "documento_pdf",
    "relatorio": "documento_pdf",
    "relatório": "documento_pdf",

    "excel": "excel",
    "xlsx": "excel",
    "xls": "excel",
    "xlsm": "excel",
    "planilha": "excel",
    "planilhas": "excel",

    "imd": "imd",
    "rgqc": "rgqc",
    "apura": "apura_sus",
    "apurasus": "apura_sus",
    "apura sus": "apura_sus",
}


@dataclass(frozen=True)
class CatalogSearchResult:
    """
    Resultado limpo para o drive_analytics.py consumir depois.
    """

    item: dict[str, Any]
    score: int
    matched_terms: list[str]

    @property
    def name(self) -> str:
        return str(self.item.get("name", ""))

    @property
    def file_id(self) -> str:
        return str(self.item.get("id", ""))

    @property
    def path(self) -> str:
        return str(self.item.get("path", ""))

    @property
    def mime_type(self) -> str:
        return str(self.item.get("mimeType", ""))

    @property
    def category(self) -> str:
        return str(self.item.get("category_detected", ""))

    @property
    def area(self) -> str:
        return str(self.item.get("area_detected", ""))

    @property
    def year(self) -> str:
        return str(self.item.get("year_detected", ""))

    @property
    def size_human(self) -> str:
        return str(self.item.get("size_human", ""))

    @property
    def modified_time(self) -> str:
        return str(self.item.get("modifiedTime", ""))

    def to_dict(self) -> dict[str, Any]:
        return {
            "score": self.score,
            "matched_terms": self.matched_terms,
            "name": self.name,
            "id": self.file_id,
            "path": self.path,
            "mimeType": self.mime_type,
            "category_detected": self.category,
            "area_detected": self.area,
            "year_detected": self.year,
            "region_or_unit_detected": self.item.get("region_or_unit_detected", ""),
            "size_human": self.size_human,
            "size_bytes": self.item.get("size_bytes", 0),
            "modifiedTime": self.modified_time,
            "extension": self.item.get("extension", ""),
            "type": self.item.get("type", ""),
        }


def normalize_text(value: Any) -> str:
    """
    Normaliza texto para busca:
    - minúsculo
    - sem acento
    - sem espaços duplicados
    """
    if value is None:
        return ""

    text = str(value).strip().lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"\s+", " ", text)
    return text


def tokenize(value: Any) -> list[str]:
    """
    Tokenização simples e estável para busca local no catálogo.
    """
    text = normalize_text(value)
    return re.findall(r"[a-zA-Z0-9_]+", text)


def extract_years(value: str) -> list[str]:
    """
    Extrai anos 20xx da pergunta.
    """
    return re.findall(r"\b(20\d{2})\b", value or "")


def load_catalog(
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Carrega o catálogo JSON gerado pelo scripts/test_gdrive.py.

    Esperado:
      scripts/drive_catalog.json

    Formato esperado:
      {
        "summary": {...},
        "items": [...]
      }
    """
    path = Path(catalog_path) if catalog_path else DEFAULT_CATALOG_JSON

    if not path.exists():
        return {
            "summary": {
                "catalog_exists": False,
                "catalog_path": str(path),
                "errors": [
                    "Catálogo não encontrado. Rode: python scripts/test_gdrive.py"
                ],
            },
            "items": [],
        }

    try:
        with path.open("r", encoding="utf-8") as f:
            payload = json.load(f)
    except Exception as e:
        return {
            "summary": {
                "catalog_exists": False,
                "catalog_path": str(path),
                "errors": [f"Falha ao ler catálogo JSON: {repr(e)}"],
            },
            "items": [],
        }

    if isinstance(payload, list):
        # fallback caso algum catálogo antigo tenha sido salvo só como lista
        return {
            "summary": {
                "catalog_exists": True,
                "catalog_path": str(path),
                "items_count": len(payload),
                "format": "legacy_list",
            },
            "items": payload,
        }

    if not isinstance(payload, dict):
        return {
            "summary": {
                "catalog_exists": False,
                "catalog_path": str(path),
                "errors": ["Formato inválido do catálogo."],
            },
            "items": [],
        }

    items = payload.get("items", [])
    summary = payload.get("summary", {})

    if not isinstance(items, list):
        items = []

    if not isinstance(summary, dict):
        summary = {}

    summary.setdefault("catalog_exists", True)
    summary.setdefault("catalog_path", str(path))
    summary.setdefault("items_count", len(items))

    return {
        "summary": summary,
        "items": items,
    }


def load_catalog_items(catalog_path: str | Path | None = None) -> list[dict[str, Any]]:
    """
    Retorna somente os itens do catálogo.
    """
    payload = load_catalog(catalog_path)
    return payload.get("items", []) or []


def load_catalog_summary(catalog_path: str | Path | None = None) -> dict[str, Any]:
    """
    Retorna somente o resumo do catálogo.
    """
    payload = load_catalog(catalog_path)
    return payload.get("summary", {}) or {}


def catalog_is_available(catalog_path: str | Path | None = None) -> bool:
    """
    True se o catálogo existe e possui itens.
    """
    payload = load_catalog(catalog_path)
    return bool(payload.get("summary", {}).get("catalog_exists")) and bool(payload.get("items"))


def is_institutional_analytics_question(message: str) -> bool:
    """
    Define se a pergunta deve ser tratada como pergunta institucional analítica.

    Essa função NÃO responde nada.
    Ela só decide se o drive_analytics.py deve assumir a pergunta.

    Exemplos que devem retornar True:
    - "analise os custos de 2024"
    - "qual indicador piorou?"
    - "compare o IMD da região oeste"
    - "quais arquivos RGQC existem?"
    """
    text = normalize_text(message)
    toks = set(tokenize(text))

    if not text:
        return False

    normalized_keywords = {normalize_text(k) for k in INSTITUTIONAL_KEYWORDS}

    if toks.intersection(normalized_keywords):
        return True

    # Expressões compostas comuns
    compound_patterns = [
        "regiao de saude",
        "regioes de saude",
        "região de saúde",
        "regiões de saúde",
        "acordo de gestao",
        "acordos de gestao",
        "acordo de gestão",
        "acordos de gestão",
        "serie historica",
        "série histórica",
        "linha de base",
        "meta pactuada",
        "resultado pactuado",
        "custo total",
        "custo medio",
        "custo médio",
        "producao ambulatorial",
        "produção ambulatorial",
        "producao hospitalar",
        "produção hospitalar",
    ]

    normalized_patterns = [normalize_text(p) for p in compound_patterns]
    return any(pattern in text for pattern in normalized_patterns)


def _item_search_blob(item: dict[str, Any]) -> str:
    """
    Junta campos relevantes em um texto único para busca.
    """
    fields = [
        item.get("name", ""),
        item.get("path", ""),
        item.get("parent_path", ""),
        item.get("mimeType", ""),
        item.get("extension", ""),
        item.get("year_detected", ""),
        item.get("area_detected", ""),
        item.get("category_detected", ""),
        item.get("region_or_unit_detected", ""),
        item.get("type", ""),
    ]
    return normalize_text(" ".join(str(f) for f in fields if f is not None))


def _score_item(
    item: dict[str, Any],
    query_terms: list[str],
    years: list[str],
    area_hint: str | None,
    category_hint: str | None,
    only_files: bool,
) -> tuple[int, list[str]]:
    """
    Calcula pontuação simples, explicável e determinística.
    """
    score = 0
    matched: list[str] = []

    blob = _item_search_blob(item)
    name = normalize_text(item.get("name", ""))
    path = normalize_text(item.get("path", ""))
    category = normalize_text(item.get("category_detected", ""))
    area = normalize_text(item.get("area_detected", ""))
    year = normalize_text(item.get("year_detected", ""))
    item_type = normalize_text(item.get("type", ""))

    if only_files and item_type == "folder":
        return 0, []

    for term in query_terms:
        if len(term) <= 1:
            continue

        if term in name:
            score += 8
            matched.append(term)
        elif term in path:
            score += 5
            matched.append(term)
        elif term in blob:
            score += 2
            matched.append(term)

    for y in years:
        if y and y == year:
            score += 15
            matched.append(y)
        elif y and y in blob:
            score += 6
            matched.append(y)

    if area_hint:
        area_norm = normalize_text(area_hint)
        if area_norm and area_norm == area:
            score += 20
            matched.append(area_hint)
        elif area_norm and area_norm in blob:
            score += 8
            matched.append(area_hint)

    if category_hint:
        category_norm = normalize_text(category_hint)
        if category_norm and category_norm == category:
            score += 20
            matched.append(category_hint)
        elif category_norm and category_norm in blob:
            score += 8
            matched.append(category_hint)

    # Priorização leve de arquivos mais úteis para análise.
    useful_categories = {"imd", "rgqc", "apura_sus", "excel", "documento_pdf"}
    if category in useful_categories:
        score += 3

    # Evitar arquivos de sistema.
    if "thumbs.db" in name:
        score -= 30

    # Evitar pastas quando existem arquivos candidatos.
    if item_type == "folder":
        score -= 2

    matched_unique = sorted(set(matched))
    return max(score, 0), matched_unique


def infer_area_hint(message: str) -> str | None:
    """
    Tenta inferir área institucional a partir da pergunta.
    """
    text = normalize_text(message)

    for key, area in AREA_ALIASES.items():
        if normalize_text(key) in text:
            return area

    return None


def infer_category_hint(message: str) -> str | None:
    """
    Tenta inferir categoria documental/dado a partir da pergunta.
    """
    text = normalize_text(message)

    for key, category in CATEGORY_ALIASES.items():
        if normalize_text(key) in text:
            return category

    return None


def search_catalog(
    query: str,
    *,
    catalog_path: str | Path | None = None,
    limit: int = 10,
    only_files: bool = True,
    min_score: int = 1,
    area_hint: str | None = None,
    category_hint: str | None = None,
    year_hint: str | int | None = None,
) -> list[CatalogSearchResult]:
    """
    Busca arquivos/pastas no catálogo.

    Esta função NÃO acessa o Google Drive.
    Ela só consulta o índice local gerado pelo scripts/test_gdrive.py.

    Parâmetros principais:
    - query: pergunta ou termo de busca.
    - limit: número máximo de resultados.
    - only_files: ignora pastas quando True.
    - area_hint: força/ajuda área, ex.: CUSTOS, GEMAG.
    - category_hint: força/ajuda categoria, ex.: imd, rgqc, apura_sus.
    - year_hint: ajuda a priorizar ano.
    """
    items = load_catalog_items(catalog_path)

    if not items:
        return []

    query_terms = tokenize(query)
    years = extract_years(query)

    if year_hint:
        years.append(str(year_hint))

    if not area_hint:
        area_hint = infer_area_hint(query)

    if not category_hint:
        category_hint = infer_category_hint(query)

    results: list[CatalogSearchResult] = []

    for item in items:
        score, matched = _score_item(
            item=item,
            query_terms=query_terms,
            years=years,
            area_hint=area_hint,
            category_hint=category_hint,
            only_files=only_files,
        )

        if score >= min_score:
            results.append(
                CatalogSearchResult(
                    item=item,
                    score=score,
                    matched_terms=matched,
                )
            )

    results.sort(
        key=lambda r: (
            r.score,
            str(r.item.get("modifiedTime", "")),
            int(r.item.get("size_bytes") or 0),
        ),
        reverse=True,
    )

    return results[: max(limit, 0)]


def search_catalog_as_dicts(
    query: str,
    *,
    catalog_path: str | Path | None = None,
    limit: int = 10,
    only_files: bool = True,
    min_score: int = 1,
    area_hint: str | None = None,
    category_hint: str | None = None,
    year_hint: str | int | None = None,
) -> list[dict[str, Any]]:
    """
    Versão serializável da busca, boa para Streamlit/session_state.
    """
    results = search_catalog(
        query=query,
        catalog_path=catalog_path,
        limit=limit,
        only_files=only_files,
        min_score=min_score,
        area_hint=area_hint,
        category_hint=category_hint,
        year_hint=year_hint,
    )
    return [r.to_dict() for r in results]


def filter_catalog(
    *,
    catalog_path: str | Path | None = None,
    area: str | None = None,
    category: str | None = None,
    year: str | int | None = None,
    mime_type: str | None = None,
    extension: str | None = None,
    only_files: bool = True,
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """
    Filtro estruturado para uso futuro em telas ou analytics.

    Exemplo:
      filter_catalog(area="CUSTOS", category="imd", year=2024)
    """
    items = load_catalog_items(catalog_path)
    out: list[dict[str, Any]] = []

    area_norm = normalize_text(area) if area else ""
    category_norm = normalize_text(category) if category else ""
    year_str = str(year) if year else ""
    mime_norm = normalize_text(mime_type) if mime_type else ""
    ext_norm = normalize_text(extension).lstrip(".") if extension else ""

    for item in items:
        if only_files and normalize_text(item.get("type")) == "folder":
            continue

        if area_norm and normalize_text(item.get("area_detected")) != area_norm:
            continue

        if category_norm and normalize_text(item.get("category_detected")) != category_norm:
            continue

        if year_str and str(item.get("year_detected", "")) != year_str:
            continue

        if mime_norm and normalize_text(item.get("mimeType")) != mime_norm:
            continue

        if ext_norm and normalize_text(item.get("extension")) != ext_norm:
            continue

        out.append(item)

        if limit is not None and len(out) >= limit:
            break

    return out


def get_catalog_overview(
    catalog_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Retorna visão resumida do catálogo para diagnóstico do MAIC.
    """
    payload = load_catalog(catalog_path)
    summary = payload.get("summary", {}) or {}
    items = payload.get("items", []) or []

    by_area: dict[str, int] = {}
    by_category: dict[str, int] = {}
    by_year: dict[str, int] = {}
    by_type: dict[str, int] = {}

    for item in items:
        area = str(item.get("area_detected") or "(não detectado)")
        category = str(item.get("category_detected") or "(não detectado)")
        year = str(item.get("year_detected") or "(não detectado)")
        item_type = str(item.get("type") or "(não detectado)")

        by_area[area] = by_area.get(area, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
        by_year[year] = by_year.get(year, 0) + 1
        by_type[item_type] = by_type.get(item_type, 0) + 1

    return {
        "catalog_available": bool(items),
        "catalog_path": summary.get("catalog_path", str(DEFAULT_CATALOG_JSON)),
        "generated_at": summary.get("generated_at", ""),
        "items_count": len(items),
        "folders_scanned": summary.get("folders_scanned", 0),
        "folders_found": summary.get("folders_found", 0),
        "files_found": summary.get("files_found", 0),
        "errors_count": summary.get("errors_count", 0),
        "errors": summary.get("errors", []),
        "by_area": by_area,
        "by_category": by_category,
        "by_year": by_year,
        "by_type": by_type,
    }


def build_context_from_results(
    results: list[CatalogSearchResult] | list[dict[str, Any]],
    *,
    max_items: int = 8,
) -> str:
    """
    Monta contexto textual curto para ser enviado ao LLM depois.

    Importante:
    Este contexto ainda NÃO é conteúdo do arquivo.
    É apenas evidência de que existem fontes candidatas no Drive.
    O drive_analytics.py depois poderá baixar/abrir os arquivos.
    """
    if not results:
        return ""

    lines = [
        "Fontes institucionais candidatas encontradas no catálogo do Google Drive:",
    ]

    for idx, result in enumerate(results[:max_items], start=1):
        if isinstance(result, CatalogSearchResult):
            data = result.to_dict()
        else:
            data = result

        lines.append(
            "\n".join(
                [
                    f"{idx}. Arquivo: {data.get('name', '')}",
                    f"   Caminho: {data.get('path', '')}",
                    f"   ID: {data.get('id', '')}",
                    f"   Tipo/MIME: {data.get('mimeType', '')}",
                    f"   Categoria: {data.get('category_detected', '')}",
                    f"   Área: {data.get('area_detected', '')}",
                    f"   Ano detectado: {data.get('year_detected', '')}",
                    f"   Unidade/Região detectada: {data.get('region_or_unit_detected', '')}",
                    f"   Modificado em: {data.get('modifiedTime', '')}",
                    f"   Score: {data.get('score', '')}",
                ]
            )
        )

    return "\n".join(lines)


def find_best_sources_for_question(
    message: str,
    *,
    catalog_path: str | Path | None = None,
    limit: int = 8,
) -> dict[str, Any]:
    """
    Função principal para o futuro drive_analytics.py.

    Retorna:
    - se o catálogo existe
    - se a pergunta parece institucional
    - fontes candidatas
    - contexto textual pronto para o LLM ou para a próxima etapa
    """
    overview = get_catalog_overview(catalog_path)
    requires_drive = is_institutional_analytics_question(message)

    if not overview["catalog_available"]:
        return {
            "requires_drive": requires_drive,
            "catalog_available": False,
            "found": False,
            "message": "Catálogo do Drive não encontrado ou vazio. Rode: python scripts/test_gdrive.py",
            "overview": overview,
            "results": [],
            "context": "",
        }

    results = search_catalog(
        query=message,
        catalog_path=catalog_path,
        limit=limit,
        only_files=True,
        min_score=1,
    )

    context = build_context_from_results(results, max_items=limit)

    return {
        "requires_drive": requires_drive,
        "catalog_available": True,
        "found": bool(results),
        "message": "Fontes candidatas encontradas." if results else "Nenhuma fonte candidata encontrada no catálogo.",
        "overview": overview,
        "results": [r.to_dict() for r in results],
        "context": context,
    }


def assert_catalog_ready(catalog_path: str | Path | None = None) -> None:
    """
    Útil para scripts/testes.
    Lança erro se catálogo não estiver pronto.
    """
    overview = get_catalog_overview(catalog_path)

    if not overview["catalog_available"]:
        raise RuntimeError(
            "Catálogo do Drive não encontrado ou vazio. "
            "Rode primeiro: python scripts/test_gdrive.py"
        )


if __name__ == "__main__":
    # Teste rápido:
    # python services/drive_catalog.py "custos IMD 2024 região oeste"
    import sys

    question = " ".join(sys.argv[1:]).strip() or "custos IMD 2024 região oeste"

    print("\n=== TESTE LOCAL DO CATÁLOGO DO DRIVE ===\n")
    print(f"Pergunta: {question}\n")

    response = find_best_sources_for_question(question)

    print("[DIAGNÓSTICO]")
    print(f"  - Catálogo disponível: {response['catalog_available']}")
    print(f"  - Pergunta exige Drive: {response['requires_drive']}")
    print(f"  - Encontrou fontes: {response['found']}")
    print(f"  - Mensagem: {response['message']}")

    print("\n[FONTES CANDIDATAS]")
    for item in response["results"]:
        print(
            f"  - score={item['score']} | {item['name']} | "
            f"ano={item['year_detected']} | categoria={item['category_detected']} | "
            f"área={item['area_detected']}"
        )
        print(f"    path={item['path']}")
        print(f"    id={item['id']}")

    print("\n[CONTEXTO GERADO]")
    print(response["context"] or "(sem contexto)")

    print("\n=== FIM ===\n")