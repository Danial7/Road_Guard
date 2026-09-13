import requests

from services.geocoder import geocode_location


GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"


# --------------------------------------------------
# KNOWN KARACHI LOCATIONS
# --------------------------------------------------

KARACHI_LOCATIONS = [
    "Nursery",
    "Drigh Road",
    "Malir Halt",
    "Star Gate",
    "Airport",
    "Karsaz",
    "Lal Kothi",
    "Regent Plaza",
    "Natha Khan",
    "Sohrab Goth",
    "Johar Mor",
    "Gulistan-e-Jauhar",
    "Gulshan-e-Iqbal",
    "Nipa",
    "University Road",
    "Saddar",
    "Tariq Road",
    "Korangi",
    "Landhi",
    "Defence",
    "Clifton",
    "Lyari",
    "SITE",
    "Mauripur",
    "Port Qasim",
]


# --------------------------------------------------
# EXTRACT SPECIFIC INCIDENT LOCATION
# --------------------------------------------------

def extract_incident_location(title):
    """
    Try to find a specific Karachi location
    mentioned in the incident title.
    """

    if not title:
        return None

    title_lower = title.lower()

    for location in KARACHI_LOCATIONS:

        if location.lower() in title_lower:
            return location

    return None


# --------------------------------------------------
# SEARCH INCIDENTS FOR ONE ROAD
# --------------------------------------------------

def search_incidents(road_name):
    """
    Search recent public reports for a specific road.
    """

    query = (
        f'"{road_name}" Karachi '
        f'(accident OR crash OR collision OR '
        f'"traffic jam" OR congestion OR '
        f'"road closure" OR "road closed" OR '
        f'construction OR diversion OR '
        f'"road blocked" OR "lane closure")'
    )

    params = {
        "query": query,
        "mode": "artlist",
        "format": "json",
        "maxrecords": 10,
        "sort": "datedesc",
        "timespan": "7d",
    }

    response = requests.get(
        GDELT_URL,
        params=params,
        timeout=15,
    )

    response.raise_for_status()

    data = response.json()

    articles = data.get(
        "articles",
        []
    )

    incidents = []

    for article in articles:

        incidents.append(
            {
                "title": article.get(
                    "title",
                    "",
                ),
                "url": article.get(
                    "url",
                    "",
                ),
                "source": article.get(
                    "domain",
                    "",
                ),
                "published": article.get(
                    "seendate",
                    "",
                ),
                "language": article.get(
                    "language",
                    "",
                ),
                "road": road_name,
            }
        )

    return incidents


# --------------------------------------------------
# ADD GEOGRAPHIC LOCATION TO INCIDENT
# --------------------------------------------------

def add_incident_location(incident):
    """
    Try to determine the geographic location
    of an incident using its title and road name.
    """

    title = incident.get(
        "title",
        "",
    )

    road_name = incident.get(
        "road",
        "",
    )

    specific_location = (
        extract_incident_location(
            title
        )
    )

    if specific_location:

        search_location = (
            f"{specific_location}, Karachi"
        )

    elif road_name:

        search_location = (
            f"{road_name}, Karachi"
        )

    else:

        search_location = ""

    updated_incident = incident.copy()

    updated_incident["incident_location"] = (
        specific_location
    )

    # No location available
    if not search_location:

        updated_incident["latitude"] = None
        updated_incident["longitude"] = None

        return updated_incident

    # Geocode the location
    location = geocode_location(
        search_location
    )

    if location:

        updated_incident["latitude"] = (
            location["latitude"]
        )

        updated_incident["longitude"] = (
            location["longitude"]
        )

    else:

        updated_incident["latitude"] = None
        updated_incident["longitude"] = None

    return updated_incident


# --------------------------------------------------
# SEARCH INCIDENTS FOR ALL ROUTE ROADS
# --------------------------------------------------

def search_route_incidents(road_names):
    """
    Search recent incidents for roads included
    in the route.
    """

    all_incidents = []

    # Limit searches to avoid excessive API requests
    roads_to_search = road_names[:10]

    for road_name in roads_to_search:

        try:

            incidents = search_incidents(
                road_name
            )

            for incident in incidents:

                incident = add_incident_location(
                    incident
                )

                all_incidents.append(
                    incident
                )

        except requests.RequestException:

            print(
                f"Could not search incidents for: "
                f"{road_name}"
            )

    return all_incidents
