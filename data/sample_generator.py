import pandas as pd
import numpy as np

def generate_sample_logs():
    np.random.seed(42)
    timestamps = pd.date_range("2026-03-20 00:00:00", periods=50, freq="30min")
    substations = ["Hamburg-Nord", "Dörpen-West", "Wahle", "Mecklar", "Grafenrheinfeld"]
    event_types = ["Thermal Overload", "Voltage Fluctuation", "Wind Feed-In Surge", "Redispatch 2.0 Requested", "Nominal Operation"]

    records = []
    for ts in timestamps:
        ev = np.random.choice(event_types, p=[0.15, 0.15, 0.25, 0.20, 0.25])
        sev = "CRITICAL" if "Overload" in ev or "Redispatch" in ev else ("WARNING" if "Voltage" in ev or "Surge" in ev else "INFO")
        feed_in_mw = int(np.random.uniform(400, 2200))
        curtailed_mw = int(feed_in_mw * np.random.uniform(0.1, 0.35)) if sev in ["WARNING", "CRITICAL"] else 0

        records.append({
            "timestamp": str(ts),
            "substation": np.random.choice(substations),
            "event_type": ev,
            "severity": sev,
            "feed_in_mw": feed_in_mw,
            "curtailed_mw": curtailed_mw
        })

    df = pd.DataFrame(records)
    df.to_csv("data/grid_incident_logs.csv", index=False)
    print("Generated sample logs: data/grid_incident_logs.csv")
    return df

if __name__ == "__main__":
    generate_sample_logs()