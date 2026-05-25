from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any


FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SLIDES_MIME = "application/vnd.google-apps.presentation"

EXCEL_MIMES = {
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-excel",
    "application/vnd.ms-excel.sheet.macroenabled.12",
}

BINARY_TEST_MIMES = {
    "application/pdf",
    "text/csv",
    *EXCEL_MIMES,
}


@dataclass
class ScanStats:
    folders_found: int = 0
    files_found: int = 0
    folders_scanned: int = 0
    errors: list[str] = field(default_factory=list)
    by_mime: Counter = field(default_factory=Counter)
    files_by_folder: dict[str, list[dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))
    catalog_items: list[dict[str, Any]] = field(default_factory=list)

    @property
    def total_found(self) -> int:
        return self.folders_found + self.files_found


def _bootstrap_import_path() -> Path:
    """
    Garante que 'services' seja importável quando rodar:
      python scripts/test_gdrive.py
    """
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    return project_root


def _load_streamlit_secrets():
    """
    Permite rodar no terminal usando o mesmo .streamlit/secrets.toml do Streamlit.
    """
    import streamlit as st  # lazy import

    _ = st.secrets  # força carregar
    return st


def _is_valid_json(s: str) -> bool:
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def _short_id(file_id: str | None) -> str:
    if not file_id:
        return "-"
    if len(file_id) <= 12:
        return file_id
    return f"{file_id[:6]}...{file_id[-6:]}"


def _safe_get(item: dict[str, Any], key: str, default: str = "") -> str:
    value = item.get(key, default)
    return "" if value is None else str(value)


def _format_size(size: Any) -> str:
    if not size:
        return "-"
    try:
        n = int(size)
    except Exception:
        return str(size)

    units = ["B", "KB", "MB", "GB"]
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{n} B"


def _size_to_int(size: Any) -> int:
    if not size:
        return 0
    try:
        return int(size)
    except Exception:
        return 0


def _print_file_line(item: dict[str, Any], indent: int = 0, show_ids: bool = True) -> None:
    prefix = "  " * indent
    name = _safe_get(item, "name", "(sem nome)")
    mime = _safe_get(item, "mimeType", "(sem mimeType)")
    file_id = _safe_get(item, "id", "")
    modified = _safe_get(item, "modifiedTime", "-")
    size = _format_size(item.get("size"))

    icon = "📁" if mime == FOLDER_MIME else "📄"

    if show_ids:
        print(f"{prefix}{icon} {name} | mime={mime} | size={size} | modified={modified} | id={file_id}")
    else:
        print(f"{prefix}{icon} {name} | mime={mime} | size={size} | modified={modified} | id={_short_id(file_id)}")


def _normalize_text(value: str) -> str:
    return (value or "").strip().lower()


def _extract_year(value: str) -> str:
    """
    Detecta ano no nome ou caminho do arquivo/pasta.
    Retorna string para facilitar gravação em CSV.
    """
    if not value:
        return ""

    years = re.findall(r"\b(20\d{2})\b", value)
    if not years:
        return ""

    # Pega o último ano encontrado, geralmente o mais específico no nome do arquivo.
    return years[-1]


def _detect_extension(name: str) -> str:
    suffix = Path(name).suffix.lower().strip(".")
    return suffix


def _detect_area(path: str, name: str) -> str:
    text = _normalize_text(f"{path} {name}")

    if "gemag" in text:
        return "GEMAG"
    if "gemap" in text:
        return "GEMAP"
    if "gemac" in text:
        return "GEMAC"
    if "custo" in text or "apura" in text or "imd" in text or "rgqc" in text:
        return "CUSTOS"
    if "pdf" in text:
        return "PDF"
    if "sheet" in text or "planilha" in text:
        return "SHEETS"
    if "doc" in text or "documento" in text:
        return "DOCS"
    if "export" in text:
        return "EXPORTS"

    return ""


def _detect_category(path: str, name: str, mime: str) -> str:
    text = _normalize_text(f"{path} {name}")

    if mime == FOLDER_MIME:
        return "pasta"
    if mime == "application/pdf":
        return "documento_pdf"
    if mime == GOOGLE_DOC_MIME:
        return "google_doc"
    if mime == GOOGLE_SHEET_MIME:
        return "google_sheet"
    if mime == GOOGLE_SLIDES_MIME:
        return "google_slides"
    if mime in EXCEL_MIMES:
        if "rgqc" in text:
            return "rgqc"
        if "imd" in text:
            return "imd"
        if "apura" in text:
            return "apura_sus"
        if "plan" in text or "planilha" in text:
            return "planilha_unidade"
        return "excel"
    if mime == "text/csv":
        return "csv"

    if "thumbs.db" in text:
        return "arquivo_sistema"

    return "outros"


def _detect_region_or_unit(path: str, name: str) -> str:
    text = f"{path}/{name}".upper()

    candidates = [
        "REGIÃO CENTRAL",
        "REGIAO CENTRAL",
        "REGIÃO CENTRO-SUL",
        "REGIAO CENTRO-SUL",
        "REGIÃO LESTE",
        "REGIAO LESTE",
        "REGIÃO NORTE",
        "REGIAO NORTE",
        "REGIÃO OESTE",
        "REGIAO OESTE",
        "REGIÃO SUDOESTE",
        "REGIAO SUDOESTE",
        "REGIÃO SUL",
        "REGIAO SUL",
        "SRS CENTRAL",
        "SRS CENTRO-SUL",
        "SRS LESTE",
        "SRS NORTE",
        "SRS OESTE",
        "SRS SUDOESTE",
        "SRS SUL",
        "SAMU",
        "HUB",
        "HCB",
        "HMIB",
        "IGESDF",
        "HSVP",
        "HAB",
        "HRAN",
        "HRGU",
        "HRL",
        "HRC",
        "HRPL",
    ]

    for candidate in candidates:
        if candidate in text:
            return candidate

    # Alguns arquivos usam siglas no nome: SRSCE, SRSCS, SRSNO, SRSOE etc.
    siglas = re.findall(r"\b(SRS[A-Z]{2,4})\b", text)
    if siglas:
        return siglas[0]

    return ""


def _build_catalog_record(
    *,
    item: dict[str, Any],
    parent_path: str,
    depth: int,
    root_folder_id: str,
    shared_drive_id: str | None,
) -> dict[str, Any]:
    name = _safe_get(item, "name", "(sem nome)")
    mime = _safe_get(item, "mimeType")
    file_id = _safe_get(item, "id")
    modified = _safe_get(item, "modifiedTime")
    size_raw = item.get("size")
    full_path = f"{parent_path}/{name}"

    owners = item.get("owners") or []
    owner_names = []
    owner_emails = []

    if isinstance(owners, list):
        for owner in owners:
            if isinstance(owner, dict):
                display_name = owner.get("displayName")
                email = owner.get("emailAddress")
                if display_name:
                    owner_names.append(str(display_name))
                if email:
                    owner_emails.append(str(email))

    return {
        "name": name,
        "id": file_id,
        "mimeType": mime,
        "type": "folder" if mime == FOLDER_MIME else "file",
        "extension": _detect_extension(name),
        "path": full_path,
        "parent_path": parent_path,
        "depth": depth,
        "size_bytes": _size_to_int(size_raw),
        "size_human": _format_size(size_raw),
        "modifiedTime": modified,
        "year_detected": _extract_year(full_path),
        "area_detected": _detect_area(parent_path, name),
        "category_detected": _detect_category(parent_path, name, mime),
        "region_or_unit_detected": _detect_region_or_unit(parent_path, name),
        "root_folder_id": root_folder_id,
        "shared_drive_id": shared_drive_id or "",
        "owner_names": "; ".join(owner_names),
        "owner_emails": "; ".join(owner_emails),
    }


def _scan_folder_recursive(
    *,
    list_files_in_folder,
    folder_id: str,
    folder_name: str,
    shared_drive_id: str | None,
    stats: ScanStats,
    depth: int,
    max_depth: int,
    show_ids: bool,
    visited: set[str],
    path: str,
    root_folder_id: str,
) -> None:
    if folder_id in visited:
        print(f"{'  ' * depth}[AVISO] Pasta já visitada, pulando para evitar ciclo: {folder_name} | id={folder_id}")
        return

    visited.add(folder_id)

    print(f"\n{'  ' * depth}📂 Varredura: {path}")
    print(f"{'  ' * depth}   id={folder_id}")

    try:
        children = list_files_in_folder(folder_id, shared_drive_id=shared_drive_id)
        stats.folders_scanned += 1
    except Exception as e:
        msg = f"Falhou listar pasta '{path}' | id={folder_id} | erro={repr(e)}"
        stats.errors.append(msg)
        print(f"{'  ' * depth}   [ERRO] {msg}")
        return

    if not children:
        print(f"{'  ' * depth}   (vazia)")
        return

    print(f"{'  ' * depth}   OK: {len(children)} item(ns) encontrado(s)")

    folders: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []

    for item in children:
        mime = _safe_get(item, "mimeType")
        stats.by_mime[mime] += 1
        stats.files_by_folder[path].append(item)

        record = _build_catalog_record(
            item=item,
            parent_path=path,
            depth=depth + 1,
            root_folder_id=root_folder_id,
            shared_drive_id=shared_drive_id,
        )
        stats.catalog_items.append(record)

        if mime == FOLDER_MIME:
            stats.folders_found += 1
            folders.append(item)
        else:
            stats.files_found += 1
            files.append(item)

    if folders:
        print(f"{'  ' * depth}   Pastas:")
        for folder in folders:
            _print_file_line(folder, indent=depth + 2, show_ids=show_ids)

    if files:
        print(f"{'  ' * depth}   Arquivos:")
        for file in files:
            _print_file_line(file, indent=depth + 2, show_ids=show_ids)

    if depth >= max_depth:
        if folders:
            print(f"{'  ' * depth}   [AVISO] Profundidade máxima atingida; subpastas não foram abertas aqui.")
        return

    for folder in folders:
        child_name = _safe_get(folder, "name", "(sem nome)")
        child_id = _safe_get(folder, "id")
        child_path = f"{path}/{child_name}"
        _scan_folder_recursive(
            list_files_in_folder=list_files_in_folder,
            folder_id=child_id,
            folder_name=child_name,
            shared_drive_id=shared_drive_id,
            stats=stats,
            depth=depth + 1,
            max_depth=max_depth,
            show_ids=show_ids,
            visited=visited,
            path=child_path,
            root_folder_id=root_folder_id,
        )


def _find_items_by_mime(stats: ScanStats, mime_types: set[str]) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for items in stats.files_by_folder.values():
        for item in items:
            if _safe_get(item, "mimeType") in mime_types:
                found.append(item)
    return found


def _find_first_by_mime(stats: ScanStats, mime_types: set[str]) -> dict[str, Any] | None:
    items = _find_items_by_mime(stats, mime_types)
    return items[0] if items else None


def _print_summary(stats: ScanStats) -> None:
    print("\n[RESUMO DA VARREDURA]")
    print(f"  - Pastas abertas com sucesso: {stats.folders_scanned}")
    print(f"  - Pastas encontradas: {stats.folders_found}")
    print(f"  - Arquivos encontrados: {stats.files_found}")
    print(f"  - Total de itens encontrados: {stats.total_found}")
    print(f"  - Erros encontrados: {len(stats.errors)}")

    print("\n[RESUMO POR MIME TYPE]")
    if not stats.by_mime:
        print("  (nenhum item classificado)")
    else:
        for mime, count in stats.by_mime.most_common():
            print(f"  - {mime}: {count}")

    print("\n[RESUMO POR PASTA]")
    if not stats.files_by_folder:
        print("  (nenhuma pasta com itens)")
    else:
        for folder_path, items in stats.files_by_folder.items():
            counter = Counter(_safe_get(i, "mimeType") for i in items)
            print(f"  - {folder_path}: {len(items)} item(ns)")
            for mime, count in counter.most_common():
                print(f"      {mime}: {count}")

    print("\n[ERROS]")
    if not stats.errors:
        print("  Nenhum erro durante a varredura.")
    else:
        for idx, error in enumerate(stats.errors, start=1):
            print(f"  {idx}. {error}")


def _build_catalog_summary(stats: ScanStats, *, generated_at: str) -> dict[str, Any]:
    by_category = Counter(item["category_detected"] for item in stats.catalog_items)
    by_area = Counter(item["area_detected"] or "(não detectado)" for item in stats.catalog_items)
    by_year = Counter(item["year_detected"] or "(não detectado)" for item in stats.catalog_items)
    by_type = Counter(item["type"] for item in stats.catalog_items)

    return {
        "generated_at": generated_at,
        "folders_scanned": stats.folders_scanned,
        "folders_found": stats.folders_found,
        "files_found": stats.files_found,
        "total_found": stats.total_found,
        "errors_count": len(stats.errors),
        "by_type": dict(by_type),
        "by_mime": dict(stats.by_mime),
        "by_category_detected": dict(by_category),
        "by_area_detected": dict(by_area),
        "by_year_detected": dict(by_year),
        "errors": stats.errors,
    }


def _write_catalog_files(
    *,
    stats: ScanStats,
    scripts_dir: Path,
    generated_at: str,
) -> tuple[Path, Path, Path]:
    """
    Sempre substitui os catálogos anteriores dentro da pasta scripts.
    """
    json_path = scripts_dir / "drive_catalog.json"
    csv_path = scripts_dir / "drive_catalog.csv"
    summary_path = scripts_dir / "drive_catalog_summary.json"

    summary = _build_catalog_summary(stats, generated_at=generated_at)

    payload = {
        "summary": summary,
        "items": stats.catalog_items,
    }

    with json_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    fieldnames = [
        "name",
        "id",
        "mimeType",
        "type",
        "extension",
        "path",
        "parent_path",
        "depth",
        "size_bytes",
        "size_human",
        "modifiedTime",
        "year_detected",
        "area_detected",
        "category_detected",
        "region_or_unit_detected",
        "root_folder_id",
        "shared_drive_id",
        "owner_names",
        "owner_emails",
    ]

    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore", delimiter=";")
        writer.writeheader()
        for item in stats.catalog_items:
            writer.writerow(item)

    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    return json_path, csv_path, summary_path


def _test_first_binary(download_file, stats: ScanStats) -> None:
    print("\n[TESTE] Download do primeiro arquivo binário suportado")

    first = _find_first_by_mime(stats, BINARY_TEST_MIMES)

    if not first:
        print("  (nenhum PDF/CSV/XLSX/XLSM encontrado para testar download)")
        return

    name = _safe_get(first, "name", "(sem nome)")
    file_id = _safe_get(first, "id")
    mime = _safe_get(first, "mimeType")

    try:
        data = download_file(file_id)
        print(f"  OK: baixou {len(data)} bytes | {name} | mime={mime} | id={file_id}")
    except Exception as e:
        print(f"  [ERRO] Falhou baixar arquivo | {name} | id={file_id} | erro={repr(e)}")


def _test_first_sheet(read_sheet_values, stats: ScanStats, range_a1: str) -> None:
    print("\n[TESTE] Leitura da primeira Google Sheet encontrada")

    first = _find_first_by_mime(stats, {GOOGLE_SHEET_MIME})

    if not first:
        print("  (nenhuma Google Sheet encontrada)")
        return

    name = _safe_get(first, "name", "(sem nome)")
    sheet_id = _safe_get(first, "id")

    try:
        values = read_sheet_values(sheet_id, range_a1)
        print(f"  OK: leu {len(values)} linha(s) | {name} | range={range_a1} | id={sheet_id}")
        for row in values[:10]:
            print("   ", row)
        if len(values) > 10:
            print(f"   ... +{len(values) - 10} linha(s)")
    except Exception as e:
        print(f"  [ERRO] Falhou ler Google Sheet | {name} | id={sheet_id} | erro={repr(e)}")


def _test_manual_sheet(read_sheet_values, spreadsheet_id: str, range_a1: str) -> None:
    print("\n[TESTE] Google Sheets manual")
    try:
        values = read_sheet_values(spreadsheet_id, range_a1)
        print(f"  OK: valores {range_a1}:")
        for row in values:
            print("   ", row)
    except Exception as e:
        print("  [ERRO] Falhou ler planilha:", repr(e))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Teste institucional Google Drive/Sheets do MAIC-Ai com varredura recursiva e geração de catálogo."
    )

    parser.add_argument(
        "--max-depth",
        type=int,
        default=10,
        help="Profundidade máxima da varredura de subpastas. Padrão: 10.",
    )

    parser.add_argument(
        "--hide-full-ids",
        action="store_true",
        help="Oculta IDs completos no terminal, exibindo somente versão curta.",
    )

    parser.add_argument(
        "--test-download",
        action="store_true",
        help="Tenta baixar o primeiro arquivo binário encontrado: PDF, CSV, XLS ou XLSX/XLSM.",
    )

    parser.add_argument(
        "--test-first-sheet",
        action="store_true",
        help="Tenta ler a primeira Google Sheet encontrada na varredura.",
    )

    parser.add_argument(
        "--range",
        default="A1:D10",
        help="Intervalo A1 para teste de Google Sheets. Padrão: A1:D10.",
    )

    parser.add_argument(
        "spreadsheet_id",
        nargs="?",
        help="Opcional: ID de uma Google Sheet específica para testar leitura.",
    )

    parser.add_argument(
        "spreadsheet_range",
        nargs="?",
        help="Opcional: intervalo A1 da Google Sheet específica. Exemplo: A1:D10.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    generated_at = datetime.now().isoformat(timespec="seconds")

    project_root = _bootstrap_import_path()
    scripts_dir = project_root / "scripts"

    st = _load_streamlit_secrets()

    from services.gdrive import (
        download_file,
        list_files_in_folder,
        list_shared_drives,
        read_sheet_values,
    )

    print("\n=== TESTE GOOGLE DRIVE / SHEETS (MAIC) ===\n")

    gcp_raw = (st.secrets.get("GCP_SERVICE_ACCOUNT_JSON") or "").strip()
    shared_drive_id = (st.secrets.get("GDRIVE_SHARED_DRIVE_ID") or "").strip()
    folder_id = (st.secrets.get("MAIC_DATA_FOLDER_ID") or "").strip()

    print("[0] Diagnóstico de configuração:")
    print(f"  - GCP_SERVICE_ACCOUNT_JSON: {'OK' if gcp_raw and _is_valid_json(gcp_raw) else 'ERRO'}")
    print(f"  - GDRIVE_SHARED_DRIVE_ID: {'OK' if shared_drive_id else '(vazio)'}")
    print(f"  - MAIC_DATA_FOLDER_ID: {'OK' if folder_id else '(vazio)'}")

    if not gcp_raw or not _is_valid_json(gcp_raw):
        print("\n[ERRO CRÍTICO] GCP_SERVICE_ACCOUNT_JSON inválido.")
        print("Corrija o .streamlit/secrets.toml antes de testar Drive/Sheets.")
        print("\n=== FIM DO TESTE COM ERRO ===\n")
        return

    if not folder_id:
        print("\n[ERRO CRÍTICO] MAIC_DATA_FOLDER_ID não está definido no secrets.toml.")
        print("\n=== FIM DO TESTE COM ERRO ===\n")
        return

    print("\n[1] Shared Drives visíveis para a Service Account:")
    try:
        drives = list_shared_drives()
        if not drives:
            print("  - (vazio) -> Service Account não enxerga nenhum Shared Drive.")
            print("    Isso é aceitável se a pasta MAIC_DATA_FOLDER_ID foi compartilhada diretamente com ela.")
        else:
            for d in drives[:50]:
                print(f"  - {d.get('name')} | id={d.get('id')}")
    except Exception as e:
        print("  [ERRO] Falhou listar Shared Drives:", repr(e))
        print("  O teste continuará tentando listar a pasta MAIC_DATA_FOLDER_ID.")

    print("\n[2] Varredura completa da pasta MAIC_DATA_FOLDER_ID e subpastas:")

    stats = ScanStats()

    _scan_folder_recursive(
        list_files_in_folder=list_files_in_folder,
        folder_id=folder_id,
        folder_name="MAIC_DATA",
        shared_drive_id=shared_drive_id or None,
        stats=stats,
        depth=0,
        max_depth=max(0, args.max_depth),
        show_ids=not args.hide_full_ids,
        visited=set(),
        path="MAIC_DATA",
        root_folder_id=folder_id,
    )

    _print_summary(stats)

    print("\n[3] Arquivos estratégicos encontrados")

    pdfs = _find_items_by_mime(stats, {"application/pdf"})
    sheets = _find_items_by_mime(stats, {GOOGLE_SHEET_MIME})
    docs = _find_items_by_mime(stats, {GOOGLE_DOC_MIME})
    slides = _find_items_by_mime(stats, {GOOGLE_SLIDES_MIME})
    csvs = _find_items_by_mime(stats, {"text/csv"})
    excel = _find_items_by_mime(stats, EXCEL_MIMES)

    print(f"  - PDFs: {len(pdfs)}")
    print(f"  - Google Sheets: {len(sheets)}")
    print(f"  - Google Docs: {len(docs)}")
    print(f"  - Google Slides: {len(slides)}")
    print(f"  - CSVs: {len(csvs)}")
    print(f"  - Excel/XLS/XLSX/XLSM: {len(excel)}")

    if pdfs:
        print("\n  PDFs encontrados:")
        for item in pdfs[:20]:
            print(f"   - {_safe_get(item, 'name')} | id={_safe_get(item, 'id')}")
        if len(pdfs) > 20:
            print(f"   ... +{len(pdfs) - 20} PDF(s)")

    if sheets:
        print("\n  Google Sheets encontradas:")
        for item in sheets[:20]:
            print(f"   - {_safe_get(item, 'name')} | id={_safe_get(item, 'id')}")
        if len(sheets) > 20:
            print(f"   ... +{len(sheets) - 20} planilha(s)")

    if docs:
        print("\n  Google Docs encontrados:")
        for item in docs[:20]:
            print(f"   - {_safe_get(item, 'name')} | id={_safe_get(item, 'id')}")
        if len(docs) > 20:
            print(f"   ... +{len(docs) - 20} documento(s)")

    print("\n[4] Gerando catálogo local dentro da pasta scripts:")
    try:
        json_path, csv_path, summary_path = _write_catalog_files(
            stats=stats,
            scripts_dir=scripts_dir,
            generated_at=generated_at,
        )
        print(f"  OK: catálogo JSON substituído em: {json_path}")
        print(f"  OK: catálogo CSV substituído em: {csv_path}")
        print(f"  OK: resumo JSON substituído em: {summary_path}")
    except Exception as e:
        print("  [ERRO] Falhou gerar catálogo local:", repr(e))

    if args.test_download:
        _test_first_binary(download_file, stats)

    if args.test_first_sheet:
        _test_first_sheet(read_sheet_values, stats, args.range)

    if args.spreadsheet_id:
        range_a1 = args.spreadsheet_range or args.range
        _test_manual_sheet(read_sheet_values, args.spreadsheet_id.strip(), range_a1.strip())
    else:
        print("\n[5] Teste Google Sheets manual opcional:")
        print("  Para testar uma planilha específica, rode:")
        print("  python scripts/test_gdrive.py <SPREADSHEET_ID> A1:D10")
        print("\n  Para testar automaticamente a primeira Google Sheet encontrada, rode:")
        print("  python scripts/test_gdrive.py --test-first-sheet")

    print("\n=== FIM DO TESTE ===\n")


if __name__ == "__main__":
    main()