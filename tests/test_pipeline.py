from pathlib import Path

import pandas as pd
import pytest

from data.export_powerbi import build_star_schema
from data.sample_generator import generate_sample_logs
from report_generator import GridReportAutomation

PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def load(name):
    return pd.read_csv(PROCESSED / f"{name}.csv")


@pytest.fixture
def logs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "data").mkdir()
    return generate_sample_logs()


def test_export_reproduces_committed_tables(logs):
    for name, table in build_star_schema(logs).items():
        pd.testing.assert_frame_equal(
            table.reset_index(drop=True), load(name), check_dtype=False
        )


def test_documented_figures(logs):
    """These figures are quoted in the Power BI README."""
    kpis = GridReportAutomation().compute_kpis(logs)
    assert kpis == {
        "total_events": 50,
        "critical_events": 25,
        "warning_events": 17,
        "total_curtailment_mwh": 6262.0,
        "top_stressed_substation": "Wahle",
    }


def test_data_quality_rules_hold():
    """Same rules as the Data Quality page of the Power BI report."""
    fact = load("fact_events")
    assert fact["event_id"].is_unique
    assert fact["timestamp"].notna().all()
    assert (fact[["feed_in_mw", "curtailed_mw"]] >= 0).all().all()
    assert (fact["curtailed_mw"] <= fact["feed_in_mw"]).all()
    assert fact["substation_id"].isin(load("dim_substation")["substation_id"]).all()
    assert fact["event_type_id"].isin(load("dim_event_type")["event_type_id"]).all()


def test_report_is_written(logs, tmp_path, monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    report = GridReportAutomation().generate_report(str(tmp_path / "out" / "briefing.md"))
    assert "ACTION REQUIRED" in report
    assert "`Wahle`" in report


def test_missing_columns_are_rejected(tmp_path):
    path = tmp_path / "bad.csv"
    pd.DataFrame({"timestamp": ["2026-03-20"]}).to_csv(path, index=False)
    with pytest.raises(ValueError, match="Missing columns"):
        GridReportAutomation(str(path)).load_and_validate_logs()
