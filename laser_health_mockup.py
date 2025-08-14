from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
import numpy as np
import datetime as dt

app = FastAPI(title="Laser Health Mockup (Single File)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/forecast")
def forecast(periods: int = 30):
    return JSONResponse(generate_mock_forecast(periods=periods))

@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Laser Health Dashboard (Mockup)</title>
  <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; margin: 0; }}
    .wrap {{ max-width: 1100px; margin: 0 auto; padding: 24px; }}
    .cards {{ display: grid; grid-template-columns: 360px 1fr; gap: 24px; align-items: start; }}
    .card {{ border: 1px solid #eaeaea; border-radius: 12px; padding: 16px; }}
    h1 {{ margin: 0 0 8px 0; }}
    h3 {{ margin: 0 0 12px 0; }}
    .muted {{ opacity: .7; }}
  </style>
</head>
<body>
  <div class="wrap">
    <header style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
      <h1>Laser Health Dashboard</h1>
      <div id="machine" class="muted"></div>
    </header>

    <section class="cards">
      <div class="card">
        <h3>Overall Health</h3>
        <div id="gauge" style="width:100%;height:260px;"></div>
        <p class="muted">Mock score from recent trend & volatility. Tune thresholds to trigger maintenance.</p>
      </div>

      <div class="card">
        <h3>Time Series + Forecast</h3>
        <div id="ts" style="width:100%;height:440px;"></div>
      </div>
    </section>
  </div>

  <script>
    async function load() {{
      const res = await fetch('/forecast')
      const data = await res.json()
      document.getElementById('machine').innerHTML = 'Machine: <strong>' + data.machine_id + '</strong>'

      const gaugeData = [{{
        type: "indicator",
        mode: "gauge+number",
        value: data.health_score,
        title: {{ text: "Health" }},
        gauge: {{
          axis: {{ range: [0, 100] }},
          steps: [
            {{ range: [0, 40], color: "#fde0dc" }},
            {{ range: [40, 70], color: "#fff3cd" }},
            {{ range: [70, 100], color: "#e6f4ea" }}
          ]
        }}
      }}]
      Plotly.newPlot('gauge', gaugeData, {{ margin: {{ t: 10, b: 10 }} }}, {{ displayModeBar: false }})

      const hist = {{
        x: data.history.dates, y: data.history.values, type: 'scatter', mode: 'lines', name: 'Actual'
      }}
      const smoothed = {{
        x: data.fitted.dates, y: data.fitted.values, type: 'scatter', mode: 'lines', name: 'Smoothed'
      }}
      const upper = {{
        x: data.forecast.dates, y: data.forecast.upper, type: 'scatter', mode: 'lines', name: 'Upper', line: {{ dash: 'dot' }}
      }}
      const lower = {{
        x: data.forecast.dates, y: data.forecast.lower, type: 'scatter', mode: 'lines', name: 'Lower', fill: 'tonexty', line: {{ dash: 'dot' }}
      }}
      const mean = {{
        x: data.forecast.dates, y: data.forecast.mean, type: 'scatter', mode: 'lines', name: 'Forecast'
      }}

      Plotly.newPlot('ts', [hist, smoothed, upper, lower, mean], {{
        margin: {{ l: 40, r: 20, t: 10, b: 40 }},
        xaxis: {{ title: 'Date' }},
        yaxis: {{ title: 'Signal' }}
      }}, {{ displayModeBar: false, responsive: true }})
    }}
    load().catch(err => {{
      document.body.innerHTML = '<pre style="color:red;padding:24px;">' + String(err) + '</pre>'
    }})
  </script>
</body>
</html>
""")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
