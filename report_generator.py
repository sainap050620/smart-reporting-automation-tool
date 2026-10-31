import os
import argparse
from datetime import datetime
import pandas as pd
from data.sample_generator import generate_sample_logs

class TenneTReportAutomation:
    """
    Automated Grid Incident & KPI Executive Reporting Engine.
    Processes raw telemetry and event logs into structured management briefs.
    """
    def __init__(self, log_path: str = "data/grid_incident_logs.csv"):
        self.log_path = log_path
        self.report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def load_and_validate_logs(self) -> pd.DataFrame:
        if not os.path.exists(self.log_path):
            generate_sample_logs()
        df = pd.read_csv(self.log_path)
        assert "timestamp" in df.columns and "event_type" in df.columns, "Schema validation failed."
        return df

    def compute_kpis(self, df: pd.DataFrame) -> dict:
        total_events = len(df)
        critical_events = int((df["severity"] == "CRITICAL").sum())
        warning_events = int((df["severity"] == "WARNING").sum())
        total_curtailment_mwh = round(df["curtailed_mw"].sum() * 0.5, 2)
        top_stressed_substation = df[df["severity"] != "INFO"]["substation"].mode()[0]

        return {
            "total_events": total_events,
            "critical_events": critical_events,
            "warning_events": warning_events,
            "total_curtailment_mwh": total_curtailment_mwh,
            "top_stressed_substation": top_stressed_substation
        }

    def synthesize_narrative(self, kpis: dict) -> str:
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            try:
                from openai import OpenAI
                client = OpenAI(api_key=api_key)
                prompt = (
                    f"You are a Senior Grid Operations Analyst. Write an executive summary bullet list "
                    f"based on these operational KPIs: {kpis}. Keep it concise, high-impact, and professional."
                )
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=250
                )
                return response.choices[0].message.content
            except Exception as e:
                print(f"API fallback triggered due to: {e}")

        return (
            f"- **Grid Stability Index:** Recorded {kpis['critical_events']} CRITICAL grid congestion incidents "
            f"and {kpis['warning_events']} stability warnings across monitored corridors.\n"
            f"- **Redispatch Volume:** Total dynamic curtailment reached {kpis['total_curtailment_mwh']:,} MWh "
            f"to safeguard transmission line limits against sudden renewable feed-in surges.\n"
            f"- **Bottleneck Area:** Substation node `{kpis['top_stressed_substation']}` experienced highest "
            f"redispatch pressure, requiring prioritized capacity allocation and Phase-Shifter Transformer adjustments."
        )

    def generate_report(self, output_path: str = "output/executive_briefing.md") -> str:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df = self.load_and_validate_logs()
        kpis = self.compute_kpis(df)
        narrative = self.synthesize_narrative(kpis)

        status_badge = "ACTION REQUIRED" if kpis["critical_events"] > 0 else "NOMINAL"
        critical_df = df[df["severity"] == "CRITICAL"][["timestamp", "substation", "event_type", "curtailed_mw"]].head(5)
        table_rows = critical_df.to_markdown(index=False) if hasattr(critical_df, "to_markdown") else critical_df.to_string(index=False)

        lines = [
            "# ⚡ Grid Operations & Redispatch 2.0 Incident Briefing",
            f"**Generated At:** {self.report_date}  ",
            f"**Status:** {status_badge}",
            "",
            "---",
            "",
            "## 1. Executive Operations Summary",
            narrative,
            "",
            "---",
            "",
            "## 2. Key Telemetry Indicators",
            "| Metric | Recorded Value | Unit |",
            "| :--- | :--- | :--- |",
            f"| **Total Monitored Incidents** | {kpis['total_events']} | Events |",
            f"| **Critical Alarm Thresholds** | {kpis['critical_events']} | Alarms |",
            f"| **Warning Thresholds** | {kpis['warning_events']} | Alarms |",
            f"| **Curtailed Renewable Power** | {kpis['total_curtailment_mwh']:,} | MWh |",
            f"| **Most Stressed Substation** | `{kpis['top_stressed_substation']}` | Facility |",
            "",
            "---",
            "",
            "## 3. High-Priority Event Log Excerpt",
            "```text",
            table_rows,
            "```",
            "",
            "---",
            "*Automated Report generated via smart-reporting-automation-tool.*",
        ]

        markdown_report = "\n".join(lines)
        with open(output_path, "w") as f:
            f.write(markdown_report)

        print(f"Report generated successfully at: {output_path}")
        return markdown_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Executive Grid Report")
    parser.add_argument("--output", default="output/executive_briefing.md", help="Output file path")
    args = parser.parse_args()

    engine = TenneTReportAutomation()
    engine.generate_report(output_path=args.output)