# app.py
import os
from collections import defaultdict, Counter
from datetime import datetime

import requests
import streamlit as st
import pandas as pd
import altair as alt
from dotenv import load_dotenv
from requests.exceptions import RequestException

# ---------------------------
# Page config & env
# ---------------------------
st.set_page_config(page_title="Weather Dashboard", page_icon="⛅", layout="wide")

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not API_KEY:
    st.error("Missing OPENWEATHER_API_KEY in .env file (add it to your .env)")
    st.stop()

# ---------------------------
# Helper: Weather API calls
# ---------------------------
def get_weather(city: str, units: str = "metric"):
    """Get current weather for a city."""
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": units}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    sys = data.get("sys", {})
    main = data.get("main", {})
    weather0 = data.get("weather", [{}])[0]

    return {
        "city": data.get("name"),
        "country": sys.get("country"),
        "temp": main.get("temp"),
        "feels_like": main.get("feels_like"),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "description": weather0.get("description"),
        "icon": weather0.get("icon"),
        "wind_speed": data.get("wind", {}).get("speed"),
        "clouds": data.get("clouds", {}).get("all"),
        "rain_1h": data.get("rain", {}).get("1h", 0) if data.get("rain") else 0,
        "sunrise": sys.get("sunrise"),
        "sunset": sys.get("sunset"),
        "dt": data.get("dt"),
    }


def get_forecast(city: str, units: str = "metric", days: int = 5):
    """Get 5-day forecast (aggregated per day)"""
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {"q": city, "appid": API_KEY, "units": units}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()

    daily = defaultdict(list)
    for item in data.get("list", []):
        ts = item.get("dt")
        if ts is None:
            continue
        date = datetime.fromtimestamp(ts).date().isoformat()
        daily[date].append(item)

    days_sorted = sorted(daily.keys())
    result = []
    for d in days_sorted[:days]:
        items = daily[d]
        temps = [x["main"]["temp"] for x in items if x.get("main")]
        rains = [x.get("rain", {}).get("3h", 0) for x in items]
        descs = [x["weather"][0]["description"] for x in items if x.get("weather")]
        icons = [x["weather"][0]["icon"] for x in items if x.get("weather")]

        if not temps:
            continue

        result.append({
            "date": d,
            "temp_min": min(temps),
            "temp_max": max(temps),
            "rain_mm": sum(rains),
            "description": Counter(descs).most_common(1)[0][0] if descs else "",
            "icon": Counter(icons).most_common(1)[0][0] if icons else None,
        })
    return result


# ---------------------------
# CSS (keeps your visual styles)
# ---------------------------
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom, #87CEEB, #E0FFFF);
        color: #333333;
        font-family: "Segoe UI", sans-serif;
    }
    h1 {
        color: #003366 !important;
        text-align: center;
        font-size: 2.4rem !important;
        font-weight: bold !important;
        margin-bottom: 12px;
    }
    h3 {
        color: #004d66 !important;
        border-bottom: 2px solid #004d66;
        padding-bottom: 4px;
    }
    .stMetric {
        background: rgba(255, 255, 255, 0.85);
        padding: 12px;
        border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    }
    .forecast-card {
        background: rgba(255, 255, 255, 0.9);
        padding: 12px;
        margin: 8px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 4px 10px rgba(0,0,0,0.12);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------
# UI: Title and inputs
# ---------------------------
st.title("🌍 Live Weather Dashboard")

col_left, col_right = st.columns([3, 1])
with col_left:
    city = st.text_input("Enter city name", "")
with col_right:
    unit_choice = st.selectbox("Units", ("Metric (°C)", "Imperial (°F)"))
units = "metric" if unit_choice.startswith("Metric") else "imperial"

if not city:
    st.info("Type a city name above (for example: 'Mumbai' or 'London') and press Enter.")
else:
    # Fetch and render
    try:
        weather = get_weather(city, units=units)
        forecast = get_forecast(city, units=units)
    except RequestException as e:
        st.error(f"Network / API error: {e}")
        st.stop()
    except Exception as e:
        st.error(f"Error fetching weather: {e}")
        st.stop()

    # safe datetime formatting
    dt_ts = weather.get("dt") or 0
    date_time = (
        datetime.fromtimestamp(dt_ts).strftime("%A, %d %b %Y %I:%M %p")
        if dt_ts
        else "N/A"
    )
    sunrise = (
        datetime.fromtimestamp(weather.get("sunrise")).strftime("%I:%M %p")
        if weather.get("sunrise")
        else "N/A"
    )
    sunset = (
        datetime.fromtimestamp(weather.get("sunset")).strftime("%I:%M %p")
        if weather.get("sunset")
        else "N/A"
    )

    # Header
    st.subheader(f"📌 {weather.get('city', city)}, {weather.get('country', '')}")
    st.caption(f"🗓 {date_time}")

    # Current weather (icon + metrics)
    col1, col2 = st.columns([1, 3])
    with col1:
        if weather.get("icon"):
            icon_url = f"http://openweathermap.org/img/wn/{weather['icon']}@4x.png"
            st.image(icon_url, width=120)
        else:
            st.write("")  # keep column height aligned
    with col2:
        temp_unit = "°C" if units == "metric" else "°F"
        temp_val = (
            f"{weather['temp']:.1f}{temp_unit}" if weather.get("temp") is not None else "N/A"
        )
        feels_val = (
            f"Feels like {weather['feels_like']:.1f}{temp_unit}"
            if weather.get("feels_like") is not None
            else ""
        )
        st.metric("Temperature", temp_val, delta=feels_val)
        desc = weather.get("description") or ""
        if desc:
            st.write(f"**{desc.title()}**")

    # Details
    st.markdown("### 📊 Current Details")
    colA, colB, colC = st.columns(3)
    colA.info(f"💧 Humidity: {weather.get('humidity', 'N/A')}%")
    wind_unit = "m/s" if units == "metric" else "mph"
    colB.info(f"🌬 Wind: {weather.get('wind_speed', 'N/A')} {wind_unit}")
    colC.info(f"⚖ Pressure: {weather.get('pressure', 'N/A')} hPa")

    colD, colE, colF = st.columns(3)
    colD.success(f"☁ Clouds: {weather.get('clouds', 'N/A')}%")
    colE.success(f"🌧 Rain (last 1h): {weather.get('rain_1h', 0)} mm")
    colF.success(f"🌅 Sunrise: {sunrise}")

    colG, colH = st.columns(2)
    colG.warning(f"🌇 Sunset: {sunset}")
    colH.warning(f"📆 Local time: {date_time}")

    # Forecast cards
    if forecast:
        st.markdown("### 🗓 5-Day Forecast")
        cols = st.columns(len(forecast))
        temp_unit = "°C" if units == "metric" else "°F"
        for c, day in zip(cols, forecast):
            with c:
                st.markdown('<div class="forecast-card">', unsafe_allow_html=True)
                st.write(f"📅 {day['date']}")
                if day.get("icon"):
                    st.image(f"http://openweathermap.org/img/wn/{day['icon']}@2x.png", width=64)
                st.write(f"**{day['description'].title()}**")
                st.write(f"🌡 Min: {day['temp_min']:.1f}{temp_unit}")
                st.write(f"🌡 Max: {day['temp_max']:.1f}{temp_unit}")
                st.write(f"🌧 Rain: {day['rain_mm']:.1f} mm")
                st.markdown('</div>', unsafe_allow_html=True)

        # Chart of trends
        st.markdown("### 📈 Forecast Trends")
        df = pd.DataFrame({
            "date": pd.to_datetime([f["date"] for f in forecast]),
            "Min Temp": [f["temp_min"] for f in forecast],
            "Max Temp": [f["temp_max"] for f in forecast],
            "Rain (mm)": [f["rain_mm"] for f in forecast],
        })
        df_melted = df.melt(id_vars=["date"], var_name="Metric", value_name="Value")

        chart = (
            alt.Chart(df_melted)
            .mark_line(point=True)
            .encode(
                x=alt.X("date:T", title="Date"),
                y=alt.Y("Value:Q", title="Value"),
                color=alt.Color("Metric:N", title="Metric"),
                tooltip=[alt.Tooltip("date:T", title="Date"),
                         alt.Tooltip("Metric:N", title="Metric"),
                         alt.Tooltip("Value:Q", title="Value")]
            )
            .interactive()
        )
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("No forecast available for this location.")