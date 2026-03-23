from flask import Flask, render_template, request
import requests
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../static")
)

def get_country_from_ip(ip):
    """Get user country code from IP using ipapi.co"""
    try:
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=3)
        data = res.json()
        return data.get("country_code", None)  # e.g., 'NZ'
    except:
        return None

def get_coords(place, country_code=None):
    """Use Nominatim to get lat/lon; bias by country_code if given."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "limit": 1}
        if country_code:
            params["countrycodes"] = country_code
        res = requests.get(url, params=params, timeout=5)
        data = res.json()
        if not data:
            return None, None
        return float(data[0]["lat"]), float(data[0]["lon"])
    except:
        return None, None

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

    # get user IP from request (x-forwarded-for on Vercel)
    ip = request.headers.get("x-forwarded-for", request.remote_addr)
    country_code = get_country_from_ip(ip)

    lat, lon = get_coords(place, country_code)
    if lat is None:
        return render_template("home.html", error="Location not found")

    weather = get_weather(lat, lon)
    if not weather:
        return render_template("home.html", error="Weather unavailable")

    return render_template(
        "result.html",
        temp=weather["temperature"],
        wind=weather["windspeed"],
        lat=lat,
        lon=lon,
        place=place
    )

app = app