"""
Tests for scripts/patch_cardsage_sync.py

Covers all three fix functions:
  patch_manifest  — adds rejected_row_count, supported_platforms, dataset_last_updated_at
  patch_facets    — converts list→dict format, adds active_on
  patch_offers    — fixes NO_CARD+bank_id offers → CREDIT
"""

import json
import sys
from pathlib import Path

import pytest

# Make the scripts directory importable
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))
import patch_cardsage_sync as pcs  # noqa: E402


# ── Helpers ────────────────────────────────────────────────────────────────────


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, indent=2))


def read_json(path: Path) -> object:
    return json.loads(path.read_text())


# ── patch_manifest ─────────────────────────────────────────────────────────────


class TestPatchManifest:
    def test_adds_missing_fields(self, tmp_path: Path) -> None:
        snap = [
            {"offer_id": "A", "platform_id": "MAKEMYTRIP"},
            {"offer_id": "B", "platform_id": "CLEARTRIP"},
            {"offer_id": "C", "platform_id": "MAKEMYTRIP"},
        ]
        manifest = {
            "schema_version": "1.1",
            "source_row_count": 10,
            "accepted_row_count": 7,
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        # Monkey-patch GEN path
        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.patch_manifest(snap)
        finally:
            pcs.GEN = original_gen

        result = read_json(tmp_path / "manifest.json")
        assert result["rejected_row_count"] == 3
        assert set(result["supported_platforms"]) == {"MAKEMYTRIP", "CLEARTRIP"}
        assert "dataset_last_updated_at" in result

    def test_overwrites_stale_values(self, tmp_path: Path) -> None:
        snap = [{"offer_id": "X", "platform_id": "YATRA"}]
        manifest = {
            "source_row_count": 5,
            "accepted_row_count": 4,
            "rejected_row_count": 99,  # stale
            "supported_platforms": ["OLD"],  # stale
            "dataset_last_updated_at": "2000-01-01",  # stale
        }
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.patch_manifest(snap)
        finally:
            pcs.GEN = original_gen

        result = read_json(tmp_path / "manifest.json")
        assert result["rejected_row_count"] == 1
        assert result["supported_platforms"] == ["YATRA"]
        assert result["dataset_last_updated_at"] != "2000-01-01"

    def test_no_platforms_in_snap(self, tmp_path: Path) -> None:
        snap: list[dict] = []
        manifest = {"source_row_count": 0, "accepted_row_count": 0}
        (tmp_path / "manifest.json").write_text(json.dumps(manifest))

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.patch_manifest(snap)
        finally:
            pcs.GEN = original_gen

        result = read_json(tmp_path / "manifest.json")
        assert result["supported_platforms"] == []
        assert result["rejected_row_count"] == 0


# ── patch_facets ───────────────────────────────────────────────────────────────


class TestPatchFacets:
    def test_builds_dict_from_snap(self, tmp_path: Path) -> None:
        snap = [
            {"platform_id": "MAKEMYTRIP", "bank_id": "HDFC"},
            {"platform_id": "MAKEMYTRIP", "bank_id": "ICICI"},
            {"platform_id": "CLEARTRIP", "bank_id": "HDFC"},
            {"platform_id": "CLEARTRIP", "bank_id": None},
        ]
        (tmp_path / "facets.snapshot.json").write_text("{}")

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.patch_facets(snap, "2026-10-28-abc123")
        finally:
            pcs.GEN = original_gen

        result = read_json(tmp_path / "facets.snapshot.json")
        assert isinstance(result["platforms"], dict)
        assert result["platforms"]["MAKEMYTRIP"]["count"] == 2
        assert result["platforms"]["CLEARTRIP"]["count"] == 2
        assert result["banks"]["HDFC"]["count"] == 2
        assert "active_on" in result
        assert result["data_version"] == "2026-10-28-abc123"

    def test_excludes_null_bank(self, tmp_path: Path) -> None:
        snap = [
            {"platform_id": "YATRA", "bank_id": None},
            {"platform_id": "YATRA", "bank_id": "AXIS"},
        ]
        (tmp_path / "facets.snapshot.json").write_text("{}")

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.patch_facets(snap, "v1")
        finally:
            pcs.GEN = original_gen

        result = read_json(tmp_path / "facets.snapshot.json")
        assert "AXIS" in result["banks"]
        assert None not in result["banks"]
        assert len(result["banks"]) == 1


# ── patch_offers ───────────────────────────────────────────────────────────────


class TestPatchOffers:
    def test_fixes_no_card_with_bank_id(self, tmp_path: Path) -> None:
        snap = [
            {"offer_id": "AIR-SBI-1", "payment_method": "NO_CARD", "bank_id": "SBI"},
            {"offer_id": "AIR-HDFC-2", "payment_method": "NO_CARD", "bank_id": "HDFC"},
            {"offer_id": "EAS-NOBANK-3", "payment_method": "NO_CARD", "bank_id": None},
            {"offer_id": "MMT-HDFC-4", "payment_method": "CREDIT", "bank_id": "HDFC"},
        ]
        snap_path = tmp_path / "offers.snapshot.json"
        snap_path.write_text(json.dumps(snap))

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            fixed = pcs.patch_offers(snap)
        finally:
            pcs.GEN = original_gen

        assert fixed == 2

        result = read_json(snap_path)
        by_id = {o["offer_id"]: o for o in result}
        assert by_id["AIR-SBI-1"]["payment_method"] == "CREDIT"
        assert by_id["AIR-HDFC-2"]["payment_method"] == "CREDIT"
        # NO_CARD + no bank_id → untouched
        assert by_id["EAS-NOBANK-3"]["payment_method"] == "NO_CARD"
        # Already CREDIT → untouched
        assert by_id["MMT-HDFC-4"]["payment_method"] == "CREDIT"

    def test_no_fixes_needed(self, tmp_path: Path) -> None:
        snap = [
            {"offer_id": "X", "payment_method": "CREDIT", "bank_id": "AXIS"},
            {"offer_id": "Y", "payment_method": "DEBIT", "bank_id": "HDFC"},
        ]
        snap_path = tmp_path / "offers.snapshot.json"
        original_text = json.dumps(snap)
        snap_path.write_text(original_text)

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            fixed = pcs.patch_offers(snap)
        finally:
            pcs.GEN = original_gen

        assert fixed == 0
        # File must NOT be rewritten when nothing changed
        assert snap_path.read_text() == original_text

    def test_air_india_emi_offers(self, tmp_path: Path) -> None:
        """The 4 known Air India EMI offers that cardsage always writes as NO_CARD."""
        air_india_ids = [
            "AIR-SBI-482A4207",
            "AIR-HDFC-2CB05313",
            "AIR-ICICI-516A3A7A",
            "AIR-AXIS-3C44AA3D",
        ]
        snap = [{"offer_id": oid, "payment_method": "NO_CARD", "bank_id": oid.split("-")[1]} for oid in air_india_ids]
        snap_path = tmp_path / "offers.snapshot.json"
        snap_path.write_text(json.dumps(snap))

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            fixed = pcs.patch_offers(snap)
        finally:
            pcs.GEN = original_gen

        assert fixed == 4
        result = read_json(snap_path)
        for offer in result:
            assert offer["payment_method"] == "CREDIT"


# ── Integration: main() end-to-end ─────────────────────────────────────────────


class TestMainIntegration:
    def test_full_pipeline(self, tmp_path: Path) -> None:
        snap = [
            {"offer_id": "AIR-SBI-482A4207", "payment_method": "NO_CARD", "bank_id": "SBI", "platform_id": "AIRINDIA"},
            {"offer_id": "MMT-ICICI-XYZ", "payment_method": "CREDIT", "bank_id": "ICICI", "platform_id": "MAKEMYTRIP"},
        ]
        (tmp_path / "offers.snapshot.json").write_text(json.dumps(snap))
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "data_version": "test-v1",
                    "source_row_count": 3,
                    "accepted_row_count": 2,
                }
            )
        )
        (tmp_path / "facets.snapshot.json").write_text("{}")

        original_gen = pcs.GEN
        pcs.GEN = tmp_path
        try:
            pcs.main()
        finally:
            pcs.GEN = original_gen

        offers = read_json(tmp_path / "offers.snapshot.json")
        by_id = {o["offer_id"]: o for o in offers}
        assert by_id["AIR-SBI-482A4207"]["payment_method"] == "CREDIT"

        manifest = read_json(tmp_path / "manifest.json")
        assert manifest["rejected_row_count"] == 1
        assert "AIRINDIA" in manifest["supported_platforms"]

        facets = read_json(tmp_path / "facets.snapshot.json")
        assert isinstance(facets["platforms"], dict)
        assert isinstance(facets["banks"], dict)
