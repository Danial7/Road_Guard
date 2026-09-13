import requests


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


def geocode_location(location_name):
    """
    Convert a location name/address into latitude and longitude.
    """

    params = {
        "q": location_name,
        "format": "json",
        "limit": 1,
    }

    headers = {
        "User-Agent": "RouteGuard/1.0"
    }

    response = requests.get(
        NOMINATIM_URL,
        params=params,
        headers=headers,
        timeout=10,
    )

    response.raise_for_status()

    results = response.json()

    if not results:
        return None

    result = results[0]

    return {
        "display_name": result["display_name"],
        "latitude": float(result["lat"]),
        "longitude": float(result["lon"]),
    }
