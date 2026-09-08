# Multi-source ingestion

**Date:** 2026-07-12

## Purpose and previous behavior

Replace a single CSV input with platform-maintained CSV, XLSX, and JSON sources without changing the canonical domain model.

## Architecture and files changed

`data/source/catalogue.yml` declares sources and platform defaults. `CsvOfferSource`, `ExcelOfferSource`, and `JsonOfferSource` produce located records that flow through shared alias normalization, Pydantic validation, duplicate detection, metadata/facet generation, and detailed reporting.

## Configuration

CSV accepts UTF-8 BOM, XLSX uses `openpyxl` and an optional sheet, and JSON accepts an array or `{ "offers": [...] }`. Explicit platform conflicts are errors; unknown fields go to `extra`.

## Test procedure and deployment

Run `python scripts/build_offer_snapshot.py`; any critical source/row failure returns non-zero. Runtime containers require only committed snapshots, not `openpyxl`.

## Known limitations and future migration

No remote downloads or scraping are performed. Add new adapters behind the same record boundary if trusted source formats evolve.
