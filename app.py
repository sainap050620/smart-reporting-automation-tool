import streamlit as st
import pandas as pd
from data.sample_generator import generate_sample_logs
from report_generator import TenneTReportAutomation

st.set_page_config(
    page_title="Grid Incident & Automation Monitor",
    page_icon="⚡",
    layout="wide"
)

st.title("⚡ TenneT Grid Incident & Automation Reporting Portal")
st.markdown("Automated operational brief generator for transmission grid events and Redispatch 2.0 incidents.")

engine = TenneTReportAutomation()
df = engine.load_and_validate_logs()
kpis = engine.compute_kpis(df)

# Top KPI metrics row
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Events", kpis["total_events"])
col2.metric("Critical Alarms", kpis["critical_events"])
col3.metric("Curtailed Volume", f"{kpis['total_curtailment_mwh']:,} MWh")
col4.metric("Stressed Substation", kpis["top_stressed_substation"])

st.markdown("---")

left_col, right_col = st.columns([1, 1])

with left_col:
    st.subheader("Substation Incident Distribution")
    sub_counts = df["substation"].value_counts().reset_index()
    sub_counts.columns = ["Substation", "Event Count"]
    st.bar_chart(data=sub_counts, x="Substation", y="Event Count")

with right_col:
    st.subheader("Executive Operations Summary")
    narrative = engine.synthesize_narrative(kpis)
    st.info(narrative)
    
    if st.button("Generate & Download Markdown Briefing"):
        report_text = engine.generate_report()
        st.download_button(
            label="Download Briefing (.md)",
            data=report_text,
            file_name="executive_briefing.md",
            mime="text/markdown"
        )

st.subheader("Raw Telemetry & Alarm Stream")
st.dataframe(df, use_container_width=True)