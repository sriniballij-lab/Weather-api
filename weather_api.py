
import requests
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)


def weather_condition(code):
    conditions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        51: "Drizzle",
        53: "Drizzle",
        55: "Drizzle",
        56: "Freezing drizzle",
        57: "Freezing drizzle",
        61: "Rain",
        63: "Rain",
        65: "Heavy rain",
        66: "Freezing rain",
        67: "Freezing rain",
        71: "Snow",
        73: "Snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Rain showers",
        81: "Rain showers",
        82: "Heavy showers",
        95: "Thunderstorm",
        96: "Thunderstorm",
        99: "Thunderstorm",
    }
    return conditions.get(code, "Unknown")


# Display the HTML
@app.route("/")
def home():
    return render_template("index.html")


# Receive coordinates from HTML
@app.route("/location", methods=["POST"])
def location():

    data = request.get_json()

    lat = data["latitude"]
    lon = data["longitude"]

    print("Latitude:", lat)
    print("Longitude:", lon)

    # Get weather
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min",
        "forecast_days": 7,
        "temperature_unit": "fahrenheit"
    }

    response = requests.get(url, params=params)

    if response.status_code != 200:
        return jsonify({"error": "Weather request failed"}), 500

    weather = response.json()

    temperature = weather["current"]["temperature_2m"]
    code = weather["current"]["weather_code"]
    condition = weather_condition(code)
    daily = weather["daily"]
    forecast = [
        {
            "date": date,
            "high": high,
            "low": low,
            "condition": weather_condition(code),
        }
        for date, high, low, code in zip(
            daily["time"],
            daily["temperature_2m_max"],
            daily["temperature_2m_min"],
            daily["weather_code"],
        )
    ]

    print(f"Temperature: {temperature}°F")
    print("Weather:", condition)

    return jsonify({
        "temperature": temperature,
        "condition": condition,
        "latitude": lat,
        "longitude": lon,
        "forecast": forecast,
    })


@app.route("/search", methods=["GET", "POST"])
def search():
    data = request.get_json(silent=True) or {}
    query = (request.args.get("query") or data.get("query", "")).strip()
    if not query:
        return jsonify({"error": "Enter a city or place."}), 400

    response = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={"name": query, "count": 5, "language": "en", "format": "json"},
    )
    if response.status_code != 200:
        return jsonify({"error": "Location search failed."}), 502

    results = response.json().get("results", [])
    if not results:
        return jsonify({"error": "Location not found."}), 404

    places = [
        {
            "name": place["name"],
            "country": place.get("country", ""),
            "admin1": place.get("admin1", ""),
            "latitude": place["latitude"],
            "longitude": place["longitude"],
        }
        for place in results
    ]
    place = places[0]
    return jsonify({
        **place,
        "results": places,
    })


# Start server
if __name__ == "__main__":
    app.run(debug=True)
