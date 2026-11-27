"""Export the event log as a star schema for the Power BI report.

Usage (from the repository root):
    python -m data.export_powerbi
"""
from pathlib import Path

import pandas as pd

from data.sample_generator import generate_sample_logs

OUTPUT = Path("data/processed")
SEVERITY_RANK = {"CRITICAL": 1, "WARNING": 2, "INFO": 3}


def build_star_schema(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Split the flat event log into one fact table and two dimensions."""
    substations = df[["substation"]].drop_duplicates().sort_values("substation").reset_index(drop=True)
    substations.insert(0, "substation_id", substations.index + 1)

    event_types = df[["event_type", "severity"]].drop_duplicates()
    event_types = event_types.sort_values("event_type").reset_index(drop=True)
    event_types.insert(0, "event_type_id", event_types.index + 1)
    event_types["severity_rank"] = event_types["severity"].map(SEVERITY_RANK)

    fact = df.assign(event_id=range(1, len(df) + 1))
    fact = fact.merge(substations, on="substation").merge(event_types, on=["event_type", "severity"])
    fact = fact.sort_values("event_id")[[
        "event_id", "timestamp", "substation_id", "event_type_id", "feed_in_mw", "curtailed_mw",
    ]]
    return {"dim_substation": substations, "dim_event_type": event_types, "fact_events": fact}


def export() -> None:
    tables = build_star_schema(generate_sample_logs())
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for name, table in tables.items():
        table.to_csv(OUTPUT / f"{name}.csv", index=False, lineterminator="\n")
        print(f"{name}: {len(table)} rows -> {OUTPUT / name}.csv")


if __name__ == "__main__":
    export()
