# fetch_weather.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY")

def get_weather(city: str, units: str = "metric"):
    if not API_KEY:
        raise RuntimeError("Set OPENWEATHER_API_KEY in .env")
    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {"q": city, "appid": API_KEY, "units": units}
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return {
        "city": data.get("name"),
        "temp": data["main"]["temp"],
        "feels_like": data["main"].get("feels_like"),
        "humidity": data["main"].get("humidity"),
        "pressure": data["main"].get("pressure"),
        "description": data["weather"][0]["description"],
        "icon": data["weather"][0]["icon"],
        "wind_speed": data.get("wind", {}).get("speed")
    }

if __name__ == "__main__":
    city = input("Enter city name: ").strip()
    try:
        w = get_weather(city)
        print(f"Weather in {w['city']}:")
        print(f"  {w['description'].title()}")
        print(f"  Temp: {w['temp']}°C (feels like {w['feels_like']}°C)")
        print(f"  Humidity: {w['humidity']}%  Wind: {w['wind_speed']} m/s")
    except requests.HTTPError as e:
        print("City not found or API error:", e)
    except Exception as e:
        print("Error:", e)