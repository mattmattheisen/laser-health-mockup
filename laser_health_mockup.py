import streamlit as st
import numpy as np
import datetime as dt
import plotly.graph_objects as go

st.set_page_config(page_title="Laser Health (Mockup)", layout="wide")

def generate_mock_forecast(periods: int = 30):
    np.random.seed(42)
    days_hist = 60
    base = 100.0
    drift = -0.12
    noise = np.random.normal(0, 0.6, days_hist)
    hist = base + drift * np.arange(days_hist) + np.cumsum(noise) * 0.2

    alpha = 0.25
    level = hist[0]
    fitted = []
    for x in hist:
        level = alpha * x + (1 - alpha) * level
        fitted.append(level)

    last = fitted[-1]
    forecast = [last for _ in range(periods)]
    std = float(np.std(hist[-20:]))
    upper = [v + 1.0 * std * (1 + i/periods) for i, v in enumerate(forecast)]
    lower = [v - 1.0 * std * (1 + i/periods) for i, v in enumerate(forecast)]

    vol_penalty = min(std / 5.0, 0.3)
    raw = max(0.0, min(1.0, (last / base) * (1 - vol_penalty)))
    health_score = int(round(raw * 100))

    today = dt.date.today()
    hist_dates = [(today - dt.timedelta(days=(len(hist) - 1 - i))).isoformat() for i in range(len(hist))]
    fut_dates = [(today + dt.timedelta(days=i+1)).isoformat() for i in range(periods)]

    return {
        "machine_id": "M-001",
        "health_score": health_score,
        "history": {"dates": hist_dates, "values": [float(x) for x in hist]},
        "fitted": {"dates": hist_dates, "values": [float(x) for x in fitted]},
        "forecast": {
            "dates": fut_dates,
            "mean": [float(x) for x in forecast],
            "upper": [float(x) for x in upper],
            "lower": [float(x) for x in lower],
        },
    }

# --- UI ---
st.title("Laser Health Dashboard — Mockup")
data = generate_mock_forecast(periods=30)

col1, col2 = st.columns([1, 2], gap="large")

with col1:
    st.subheader("Overall Health")
    gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=data["health_score"],
            title={"text": "Health"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "black"},
                "steps": [
                    {"range": [0, 40], "color": "#fde0dc"},
                    {"range": [40, 70], "color": "#fff3cd"},
                    {"range": [70, 100], "color": "#e6f4ea"},
                ],
            },
            number={"suffix": ""},
        )
    )
    gauge.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=260)
    st.plotly_chart(gauge, use_container_width=True)
    st.caption("Mock score from recent trend & volatility. Tune thresholds to trigger maintenance.")

with col2:
    st.subheader("Time Series + Forecast")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=data["history"]["dates"], y=data["history"]["values"], name="Actual", mode="lines"))
    fig.add_trace(go.Scatter(x=data["fitted"]["dates"], y=data["fitted"]["values"], name="Smoothed", mode="lines"))
    fig.add_trace(go.Scatter(x=data["forecast"]["dates"], y=data["forecast"]["upper"], name="Upper", mode="lines", line=dict(dash="dot")))
    fig.add_trace(go.Scatter(x=data["forecast"]["dates"], y=data["forecast"]["lower"], name="Lower", mode="lines", line=dict(dash="dot"), fill="tonexty"))
    fig.add_trace(go.Scatter(x=data["forecast"]["dates"], y=data["forecast"]["mean"], name="Forecast", mode="lines"))
    fig.update_layout(
        margin=dict(l=20, r=20, t=10, b=20),
        xaxis_title="Date",
        yaxis_title="Signal",
        height=440
    )
    st.plotly_chart(fig, use_container_width=True)

st.sidebar.header("Machine")
st.sidebar.write(f"**ID:** {data['machine_id']}")
st.sidebar.write(f"**Health:** {data['health_score']}/100")

st.sidebar.header("Controls")
periods = st.sidebar.slider("Forecast periods (days)", 7, 60, 30, step=1)
if st.sidebar.button("Recompute"):
    data = generate_mock_forecast(periods=periods)
    st.experimental_rerun()
