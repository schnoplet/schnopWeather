from flask import Flask, render_template, request
import requests
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../static")
)

HEADERS = {"User-Agent": "schnopWeather/1.0 (+https://yourdomain.com)"}

def get_country_from_ip(ip):
    """Get user country code from IP using ipapi.co"""
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        data = res.json()
        return data.get("country_code", None)
    except:
        return None

def get_coords(place, country_code=None):
    """Use Nominatim to get lat/lon and display name; bias by country_code if given."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "limit": 1}
        if country_code:
            params["countrycodes"] = country_code
        res = requests.get(url, params=params, timeout=5, headers=HEADERS)
        data = res.json()
        if not data:
            return None, None, None
        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])
        display_name = data[0]["display_name"]  # full resolved name
        return lat, lon, display_name
    except:
        return None, None, None

def get_weather(lat, lon):
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    try:
        res = requests.get(url, timeout=5)
        data = res.json()
        return data.get("current_weather", None)
    except:
        return None

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/weather", methods=["POST"])
def weather():
    place = request.form.get("place")
    if not place:
        return render_template("home.html", error="Please enter a location")

    ip = request.headers.get("x-forwarded-for", request.remote_addr)
    country_code = get_country_from_ip(ip)

    lat, lon, display_name = get_coords(place, country_code)
    if lat is None:
        return render_template("home.html", error="Location not found")

    weather = get_weather(lat, lon)
    if not weather:
        return render_template("home.html", error="Weather unavailable")

    # extract city + country from display_name
    # example: "Hamilton, Waikato, New Zealand" -> "Hamilton, New Zealand"
    parts = display_name.split(",")
    city_country = f"{parts[0].strip()}, {parts[-1].strip()}"

    return render_template(
        "result.html",
        temp=weather["temperature"],
        wind=weather["windspeed"],
        lat=lat,
        lon=lon,
        place=city_country
    )

app = app