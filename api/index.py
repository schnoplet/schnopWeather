from flask import Flask, render_template, request, jsonify
import requests
import os
import re

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(
    __name__,
    template_folder=TEMPLATES_DIR,
    static_folder=STATIC_DIR,
)

HEADERS = {
    "User-Agent": "schnopWeather/1.0 (Flask weather demo)"
}

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def client_ip() -> str:
    forwarded = request.headers.get("x-forwarded-for", "").strip()
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip", "").strip()
    if real_ip:
        return real_ip
    return request.remote_addr or ""


def get_country_from_ip(ip: str) -> str | None:
    if not ip or ip in {"127.0.0.1", "::1"}:
        return None

    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        data = res.json()
        cc = data.get("country_code")
        if cc and isinstance(cc, str) and len(cc) == 2:
            return cc.upper()
    except Exception:
        pass

    return None


def search_locations(query: str, country_code: str | None = None, limit: int = 6):
    params = {
        "q": query,
        "format": "jsonv2",
        "addressdetails": 1,
        "limit": limit,
    }

    if country_code and re.fullmatch(r"[A-Za-z]{2}", country_code):
        params["countrycodes"] = country_code.lower()

    try:
        res = requests.get(
            NOMINATIM_URL,
            params=params,
            headers=HEADERS,
            timeout=6,
        )
        res.raise_for_status()
        return res.json()
    except Exception:
        return []


def format_location(item: dict) -> str:
    address = item.get("address") or {}

    locality = (
        address.get("city")
        or address.get("town")
        or address.get("village")
        or address.get("hamlet")
        or address.get("municipality")
        or address.get("county")
        or address.get("state")
        or item.get("name")
    )

    country = address.get("country")

    if locality and country:
        return f"{locality}, {country}"
    if locality:
        return locality
    if country:
        return country

    display_name = item.get("display_name")
    if display_name:
        return display_name

    return "Unknown location"


def get_weather(lat: float, lon: float):
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,apparent_temperature,wind_speed_10m,weather_code,is_day",
        "wind_speed_unit": "kmh",
        "temperature_unit": "celsius",
        "timezone": "auto",
    }

    try:
        res = requests.get(
            OPEN_METEO_URL,
            params=params,
            headers=HEADERS,
            timeout=6,
        )
        res.raise_for_status()
        data = res.json()
        return data.get("current")
    except Exception:
        return None


def weather_details(code, is_day):
    try:
        code = int(code)
    except Exception:
        code = None

    day = int(is_day) == 1 if is_day is not None else True

    if code == 0:
        return ("Clear sky", "☀️" if day else "🌙")
    if code in {1, 2, 3}:
        return ("Partly cloudy", "🌤️" if day else "☁️")
    if code in {45, 48}:
        return ("Foggy", "🌫️")
    if code in {51, 53, 55}:
        return ("Drizzle", "🌦️")
    if code in {56, 57}:
        return ("Freezing drizzle", "🧊")
    if code in {61, 63, 65}:
        return ("Rain", "🌧️")
    if code in {66, 67}:
        return ("Freezing rain", "🧊")
    if code in {71, 73, 75}:
        return ("Snow", "❄️")
    if code == 77:
        return ("Snow grains", "❄️")
    if code in {80, 81, 82}:
        return ("Rain showers", "🌧️")
    if code in {85, 86}:
        return ("Snow showers", "🌨️")
    if code in {95, 96, 99}:
        return ("Thunderstorm", "⛈️")

    return ("Weather", "⛅")


@app.route("/")
def home():
    country_code = get_country_from_ip(client_ip())
    return render_template("home.html", country_code=country_code)


@app.route("/suggest")
def suggest():
    query = request.args.get("q", "").strip()
    if len(query) < 2:
        return jsonify([])

    country_code = request.args.get("country", "").strip().upper()
    if not re.fullmatch(r"[A-Za-z]{2}", country_code):
        country_code = get_country_from_ip(client_ip())

    results = search_locations(query, country_code=country_code, limit=6)

    payload = []
    for item in results:
        label = format_location(item)
        subtitle = item.get("display_name", "")
        if subtitle == label:
            subtitle = ""

        payload.append(
            {
                "label": label,
                "subtitle": subtitle,
                "query": label,
            }
        )

    return jsonify(payload)


@app.route("/weather", methods=["POST"])
def weather():
    place = request.form.get("place", "").strip()
    country_code = get_country_from_ip(client_ip())

    if not place:
        return render_template(
            "home.html",
            error="Type a location first.",
            country_code=country_code,
        )

    results = search_locations(place, country_code=country_code, limit=1)
    if not results:
        return render_template(
            "home.html",
            error="Location not found.",
            country_code=country_code,
        )

    item = results[0]
    lat = float(item["lat"])
    lon = float(item["lon"])
    resolved_place = format_location(item)

    current = get_weather(lat, lon)
    if not current:
        return render_template(
            "home.html",
            error="Weather unavailable right now.",
            country_code=country_code,
        )

    weather_label, weather_emoji = weather_details(
        current.get("weather_code"),
        current.get("is_day"),
    )

    return render_template(
        "result.html",
        resolved_place=resolved_place,
        temperature=current.get("temperature_2m"),
        feels_like=current.get("apparent_temperature"),
        wind_speed=current.get("wind_speed_10m"),
        weather_label=weather_label,
        weather_emoji=weather_emoji,
        weather_time=current.get("time"),
        lat=lat,
        lon=lon,
    )