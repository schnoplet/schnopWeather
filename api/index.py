from flask import Flask, render_template, request
import requests
import os

app = Flask(
    __name__,
    template_folder=os.path.join(os.path.dirname(__file__), "../templates"),
    static_folder=os.path.join(os.path.dirname(__file__), "../static")
)

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
    lat = request.form.get("lat")
    lon = request.form.get("lon")

    if not lat or not lon:
        return render_template("home.html", error="Location not provided")

    weather = get_weather(lat, lon)

    if not weather:
        return render_template("home.html", error="Weather unavailable")

    return render_template(
        "result.html",
        temp=weather["temperature"],
        wind=weather["windspeed"],
        lat=lat,
        lon=lon
    )

# Vercel handler
def handler(environ, start_response):
    return app(environ, start_response)