from flask import Flask, render_template, request
import requests
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../static")
)

def get_coords(place):
    """Use Nominatim API to get lat/lon from place name."""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {"q": place, "format": "json", "limit": 1}
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

    lat, lon = get_coords(place)
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