"""Regression tests for numerical safety, batch imports, and audit integrity."""
import csv
import math

import pytest
from fastapi.testclient import TestClient

from fe_urea import ValidationError, calculate_fe_urea, process_batch
from agents.api import app
from agents.base import AuditTrail


@pytest.mark.parametrize("invalid", [float("nan"), float("inf"), -float("inf"), True, False, 0, -1])
def test_reject_nonfinite_boolean_or_nonpositive(invalid):
    with pytest.raises(ValidationError):
        calculate_fe_urea(invalid, 100, 20, 100)


def test_reject_overflowed_calculation():
    with pytest.raises(ValidationError, match="not finite"):
        calculate_fe_urea(1e308, 1, 1, 1e308)


def test_report_missing_batch_measurements_without_imputation(tmp_path):
    source, destination = tmp_path / "input.csv", tmp_path / "output.csv"
    source.write_text(
        "serum_creatinine,urine_creatinine,serum_urea,urine_urea\n"
        "1,100,20,700\n1,100,,700\n1,100,20,nan\n",
        encoding="utf-8",
    )
    process_batch(str(source), str(destination))
    with destination.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert [r["classification"] for r in rows] == [
        "Acute Tubular Necrosis / Intrinsic Renal Disease",
        "INVALID_INPUT",
        "INVALID_INPUT",
    ]


def test_batch_requires_measurements(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text("identifier,serum_urea\nx,20\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="requires"):
        process_batch(str(source), str(tmp_path / "output.csv"))


def test_batch_rejects_duplicate_headers(tmp_path):
    source = tmp_path / "input.csv"
    source.write_text(
        "serum_creatinine,serum_creatinine,urine_creatinine,serum_urea,urine_urea\n"
        "1,1,100,20,200\n", encoding="utf-8")
    with pytest.raises(ValidationError, match="unique"):
        process_batch(str(source), str(tmp_path / "output.csv"))


def test_hmac_detects_field_tampering_and_copy_isolation():
    trail = AuditTrail(secret_key="unit-test-key")
    entry = trail.log("tester", "review", "CHECK", {"status": "OK"})
    assert trail.verify_integrity()
    snapshot = trail.get_trail()
    snapshot[0]["actor"] = "mutated"
    assert trail.verify_integrity()
    trail.logs[0]["actor"] = "forged"
    assert not trail.verify_integrity()
    trail.logs[0]["actor"] = "tester"
    assert trail.verify_integrity()
    trail.logs[0]["current_hash"] = "0" * 64
    assert not trail.verify_integrity()


def test_api_returns_correct_feurea_and_validates():
    client = TestClient(app)
    valid = dict(serum_creatinine=1, urine_creatinine=100,
                 serum_urea=20, urine_urea=700)
    response = client.post("/api/fe-urea", json=valid)
    assert response.status_code == 200
    assert response.json()["fe_urea_percent"] == 35
    assert client.post("/api/fe-urea", json={**valid, "serum_urea": 0}).status_code == 422
    assert client.post("/api/fe-urea", json={**valid, "serum_urea": "NaN"}).status_code == 422


def test_batch_export_escapes_spreadsheet_formula(tmp_path):
    source = tmp_path / "input.csv"
    destination = tmp_path / "out.csv"
    source.write_text(
        "label,serum_creatinine,urine_creatinine,serum_urea,urine_urea\n"
        '"=HYPERLINK(""https://example.com"")",1,100,20,100\n',
        encoding="utf-8",
    )
    process_batch(str(source), str(destination))
    with destination.open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    assert rows[0]["label"].startswith("'=HYPERLINK")


def test_very_large_int_rejected():
    with pytest.raises(ValidationError):
        calculate_fe_urea(10 ** 1000, 100, 20, 100)
