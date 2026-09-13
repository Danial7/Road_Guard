import re

from utils.distance import distance_to_route_km
from datetime import datetime, timezone


# --------------------------------------------------
# ROAD NAME NORMALIZATION
# --------------------------------------------------

def normalize_road_name(road_name):
    """
    Normalize a road name for easier comparison.
    """

    if not road_name:
        return ""

    road_name = road_name.lower()

    # Remove common punctuation
    road_name = re.sub(
        r"[-_/.,]",
        " ",
        road_name,
    )

    # Remove common road suffixes
    road_name = re.sub(
        r"\b(road|rd|street|st|avenue|ave)\b",
        "",
        road_name,
    )

    # Remove extra spaces
    road_name = re.sub(
        r"\s+",
        " ",
        road_name,
    ).strip()

    return road_name


# --------------------------------------------------
# ROAD ALIASES
# --------------------------------------------------

ROAD_ALIASES = {
    "shahrah e faisal": [
        "shahrah faisal",
        "shara e faisal",
        "shahrah e faisal road",
    ],

    "mauripur road": [
        "mauripur rd",
        "mauripur road",
    ],

    "korangi road": [
        "korangi road",
        "korangi rd",
    ],
}


# --------------------------------------------------
# ROAD MATCHING
# --------------------------------------------------

def roads_match(
    incident_road,
    route_road,
):
    """
    Check whether two road names refer
    to the same road.
    """

    incident = normalize_road_name(
        incident_road
    )

    route = normalize_road_name(
        route_road
    )

    if not incident or not route:
        return False

    # Exact normalized match
    if incident == route:
        return True

    # Partial match
    if incident in route or route in incident:
        return True

    # Alias matching
    for main_road, aliases in ROAD_ALIASES.items():

        route_group = [
            main_road,
            *aliases,
        ]

        normalized_group = [
            normalize_road_name(name)
            for name in route_group
        ]

        if (
            route in normalized_group
            and incident in normalized_group
        ):
            return True

    return False


# --------------------------------------------------
# INCIDENT KEYWORDS
# --------------------------------------------------

INCIDENT_KEYWORDS = {
    "ACCIDENT": [
        "accident",
        "crash",
        "collision",
        "hit",
        "overturned",
    ],

    "TRAFFIC_CONGESTION": [
        "traffic jam",
        "traffic congestion",
        "heavy traffic",
        "traffic gridlock",
        "congested",
        "traffic disruption",
    ],

    "ROAD_CLOSURE": [
        "road closed",
        "road closure",
        "road shut",
        "road blocked",
        "closed for traffic",
    ],

    "LANE_CLOSURE": [
        "lane closed",
        "lane closure",
        "lanes closed",
    ],

    "CONSTRUCTION": [
        "construction",
        "road work",
        "repair work",
        "development work",
        "under construction",
    ],

    "DIVERSION": [
        "diversion",
        "traffic diverted",
        "route diverted",
        "diverted traffic",
    ],

    "ROAD_BLOCKED": [
        "road blocked",
        "blocked road",
        "blocked for traffic",
        "traffic blocked",
    ],
}


# --------------------------------------------------
# INCIDENT CLASSIFICATION
# --------------------------------------------------

def classify_incident(title):
    """
    Classify an incident based on keywords
    in its title.
    """

    if not title:
        return None

    text = title.lower()

    for incident_type, keywords in INCIDENT_KEYWORDS.items():

        for keyword in keywords:

            if keyword in text:
                return incident_type

    return None


# --------------------------------------------------
# INCIDENT FRESHNESS
# --------------------------------------------------

def calculate_freshness(published_time):
    """
    Estimate how recent an incident is.
    """

    if not published_time:
        return "UNKNOWN"

    try:

        published = datetime.strptime(
            published_time,
            "%Y%m%dT%H%M%SZ",
        ).replace(
            tzinfo=timezone.utc
        )

    except ValueError:

        return "UNKNOWN"

    now = datetime.now(
        timezone.utc
    )

    age_hours = (
        now - published
    ).total_seconds() / 3600

    if age_hours <= 6:
        return "VERY_RECENT"

    if age_hours <= 24:
        return "RECENT"

    if age_hours <= 72:
        return "OLDER"

    return "STALE"


# --------------------------------------------------
# ANALYZE SINGLE INCIDENT
# --------------------------------------------------

def analyze_incident(incident):
    """
    Classify and assess the freshness
    of an incident.
    """

    incident_type = classify_incident(
        incident.get(
            "title",
            "",
        )
    )

    freshness = calculate_freshness(
        incident.get(
            "published",
            "",
        )
    )

    if incident_type is None:
        return None

    analyzed_incident = incident.copy()

    analyzed_incident["type"] = (
        incident_type
    )

    analyzed_incident["freshness"] = (
        freshness
    )

    return analyzed_incident


# --------------------------------------------------
# ROUTE RELEVANCE SCORE
# --------------------------------------------------

def calculate_route_relevance(
    incident,
    road_names,
    route_geometry=None,
):
    """
    Calculate how relevant an incident is
    to the selected route.
    """

    score = 0

    incident_road = incident.get(
        "road",
        "",
    )

    route_roads = [
        road
        for road in road_names
    ]

    # --------------------------------------------------
    # ROAD-NAME MATCHING
    # --------------------------------------------------

    for route_road in route_roads:

        if roads_match(
            incident_road,
            route_road,
        ):

            score += 30
            break

    # --------------------------------------------------
    # GEOGRAPHIC DISTANCE
    # --------------------------------------------------

    if (
        route_geometry
        and incident.get("latitude") is not None
        and incident.get("longitude") is not None
    ):

        distance = distance_to_route_km(
            incident["latitude"],
            incident["longitude"],
            route_geometry,
        )

        incident["route_distance_km"] = (
            distance
        )

        if distance <= 1:

            score += 30

        elif distance <= 3:

            score += 20

        elif distance <= 5:

            score += 10

    # --------------------------------------------------
    # FRESHNESS
    # --------------------------------------------------

    freshness = incident.get(
        "freshness"
    )

    if freshness == "VERY_RECENT":

        score += 25

    elif freshness == "RECENT":

        score += 20

    elif freshness == "OLDER":

        score += 10

    # --------------------------------------------------
    # RECOGNIZED INCIDENT
    # --------------------------------------------------

    if incident.get("type"):

        score += 10

    return score


# --------------------------------------------------
# CONFIDENCE LEVEL
# --------------------------------------------------

def get_confidence_level(score):
    """
    Convert relevance score into a confidence level.
    """

    if score >= 60:

        return "HIGH"

    if score >= 40:

        return "MEDIUM"

    if score >= 20:

        return "LOW"

    return "IGNORE"


# --------------------------------------------------
# ANALYZE ALL ROUTE INCIDENTS
# --------------------------------------------------

def analyze_route_incidents(
    incidents,
    road_names,
    route_geometry=None,
):
    """
    Analyze incidents and keep those relevant
    to the route.
    """

    analyzed_incidents = []

    for incident in incidents:

        analyzed = analyze_incident(
            incident
        )

        if analyzed is None:

            continue

        score = calculate_route_relevance(
            analyzed,
            road_names,
            route_geometry,
        )

        confidence = get_confidence_level(
            score
        )

        if confidence == "IGNORE":

            continue

        analyzed["relevance_score"] = (
            score
        )

        analyzed["confidence"] = (
            confidence
        )

        analyzed_incidents.append(
            analyzed
        )

    return analyzed_incidents
