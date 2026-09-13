import requests
import streamlit as st


TOMTOM_TRAFFIC_URL = (
    "https://api.tomtom.com/traffic/services/5/incidentDetails"
)


def get_tomtom_incidents(route_geometry):
    """
    Retrieve TomTom traffic incidents around the route.
    Returns an empty list if TomTom is unavailable.
    """

    try:
        api_key = st.secrets["TOMTOM_API_KEY"]
    except Exception:
        return []

    coordinates = route_geometry.get("coordinates", [])

    if not coordinates:
        return []

    longitudes = [point[0] for point in coordinates]
    latitudes = [point[1] for point in coordinates]

    min_latitude = min(latitudes)
    max_latitude = max(latitudes)
    min_longitude = min(longitudes)
    max_longitude = max(longitudes)

    # Add a small buffer around the route.
    buffer = 0.03

    bbox = (
        f"{min_latitude - buffer},"
        f"{min_longitude - buffer},"
        f"{max_latitude + buffer},"
        f"{max_longitude + buffer}"
    )

    params = {
        "key": api_key,
        "bbox": bbox,
        "fields": (
            "{incidents{"
            "type,"
            "geometry{type,coordinates},"
            "properties{"
            "id,"
            "iconCategory,"
            "magnitudeOfDelay,"
            "length,"
            "delay,"
            "events{description,code}"
            "}"
            "}}"
        ),
        "language": "en-GB",
        "timeValidityFilter": "present",
    }

    try:
        response = requests.get(
            TOMTOM_TRAFFIC_URL,
            params=params,
            timeout=15,
        )

        response.raise_for_status()

        data = response.json()

    except Exception:
        return []

    return parse_tomtom_incidents(data)


def parse_tomtom_incidents(data):
    incidents = []

    raw_incidents = data.get("incidents", [])

    for item in raw_incidents:

        properties = item.get("properties", {})

        events = properties.get("events", [])

        description = "Traffic incident"

        if events:
            description = events[0].get(
                "description",
                "Traffic incident",
            )

        incidents.append(
            {
                "source": "TomTom",
                "id": properties.get("id"),
                "description": description,
                "icon_category": properties.get(
                    "iconCategory"
                ),
                "magnitude_of_delay": properties.get(
                    "magnitudeOfDelay"
                ),
                "length_meters": properties.get(
                    "length"
                ),
                "delay_seconds": properties.get(
                    "delay"
                ),
                "geometry": item.get("geometry"),
            }
        )

    return incidents
