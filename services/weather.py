import requests


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


def get_weather_description(weather_code):
    """
    Convert Open-Meteo weather code into a readable description.
    """

    weather_descriptions = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Fog",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snowfall",
        73: "Moderate snowfall",
        75: "Heavy snowfall",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    return weather_descriptions.get(
        weather_code,
        "Unknown weather condition",
    )


def get_weather(latitude, longitude):
    """
    Get current weather for a latitude and longitude
    using Open-Meteo.
    """

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "weather_code,"
            "wind_speed_10m"
        ),
        "timezone": "auto",
    }

    response = requests.get(
        OPEN_METEO_URL,
        params=params,
        timeout=10,
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]

    weather_code = current["weather_code"]

    return {
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "weather_code": weather_code,
        "description": get_weather_description(weather_code),
        "wind_speed": current["wind_speed_10m"],
    }
