import requests
import streamlit as st

from streamlit_geolocation import streamlit_geolocation

from services.geocoder import geocode_location
from services.router import (
    get_route,
    get_route_road_names,
)
from services.weather import get_weather
from services.incident_search import search_route_incidents
from services.incident_analyzer import analyze_route_incidents
from ui.map import display_route_map
from ui.travel_brief import generate_travel_brief


# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="RouteGuard",
    page_icon="🚗",
    layout="wide",
)


# --------------------------------------------------
# SESSION STATE
# --------------------------------------------------

if "route_data" not in st.session_state:
    st.session_state.route_data = None

if "route_planned" not in st.session_state:
    st.session_state.route_planned = False


# --------------------------------------------------
# HEADER
# --------------------------------------------------

st.title("🚗 RouteGuard")

st.caption(
    "Smart Route & Travel Alert Assistant"
)

st.write(
    "Plan your journey, check current conditions, "
    "and get alerts about potential route disruptions."
)

st.divider()


# --------------------------------------------------
# CURRENT LOCATION
# --------------------------------------------------

st.subheader("📍 Current Location")

gps_location = streamlit_geolocation()

if (
    gps_location
    and gps_location.get("latitude") is not None
):
    st.success("📍 Current location detected.")

    gps_latitude = gps_location["latitude"]
    gps_longitude = gps_location["longitude"]

    st.write(
        f"Latitude: {gps_latitude:.6f}"
    )

    st.write(
        f"Longitude: {gps_longitude:.6f}"
    )

else:
    gps_latitude = None
    gps_longitude = None

    st.info(
        "GPS location is not available. "
        "You can enter your location manually below."
    )


# --------------------------------------------------
# MANUAL CURRENT LOCATION
# --------------------------------------------------

current_location = st.text_input(
    "Or enter your location manually",
    placeholder="Example: Gulistan-e-Jauhar, Karachi",
)


# --------------------------------------------------
# DESTINATION
# --------------------------------------------------

destination = st.text_input(
    "🏁 Destination",
    placeholder="Example: Port Qasim, Karachi",
)


# --------------------------------------------------
# PLAN ROUTE BUTTON
# --------------------------------------------------

if st.button(
    "🚗 Plan My Route",
    type="primary",
):

    # Clear the previous result before starting
    st.session_state.route_data = None
    st.session_state.route_planned = False

    # --------------------------------------------------
    # INPUT VALIDATION
    # --------------------------------------------------

    if (
        gps_latitude is None
        and not current_location.strip()
    ) or not destination.strip():

        st.warning(
            "Please use your current GPS location "
            "or enter your current location manually, "
            "and enter a destination."
        )

    else:

        origin = None
        destination_data = None
        route = None
        road_names = []
        route_incidents = []
        weather = None

        # --------------------------------------------------
        # GEOCODING
        # --------------------------------------------------

        with st.spinner("Finding locations..."):

            try:

                # Use GPS coordinates if available
                if (
                    gps_latitude is not None
                    and gps_longitude is not None
                ):
                    origin = {
                        "display_name": "Current GPS Location",
                        "latitude": gps_latitude,
                        "longitude": gps_longitude,
                    }

                # Otherwise geocode manual location
                else:
                    origin = geocode_location(
                        current_location.strip()
                    )

                # Geocode destination
                destination_data = geocode_location(
                    destination.strip()
                )

            except requests.RequestException:
                st.error(
                    "Unable to contact the location "
                    "service. Please try again later."
                )

        # --------------------------------------------------
        # LOCATION VALIDATION
        # --------------------------------------------------

        if origin is None:

            st.error(
                f"Could not find: {current_location}"
            )

        elif destination_data is None:

            st.error(
                f"Could not find: {destination}"
            )

        else:

            st.success(
                "Both locations found successfully!"
            )

            # --------------------------------------------------
            # ROUTE CALCULATION
            # --------------------------------------------------

            with st.spinner("Calculating route..."):

                try:
                    route = get_route(
                        origin,
                        destination_data,
                    )

                except requests.RequestException:
                    st.error(
                        "Unable to contact the routing "
                        "service. Please try again later."
                    )
                    route = None

            # --------------------------------------------------
            # ROUTE VALIDATION
            # --------------------------------------------------

            if route is None:

                st.error(
                    "Unable to calculate a route "
                    "between these locations."
                )

            else:

                st.success(
                    "Route calculated successfully!"
                )

                # --------------------------------------------------
                # ROUTE ROAD NAMES
                # --------------------------------------------------

                road_names = get_route_road_names(
                    route["steps"]
                )

                # --------------------------------------------------
                # ROUTE ALERTS
                # --------------------------------------------------

                with st.spinner(
                    "Searching for recent incidents "
                    "on your route..."
                ):

                    try:

                        raw_incidents = (
                            search_route_incidents(
                                road_names
                            )
                        )

                        route_incidents = (
                            analyze_route_incidents(
                                raw_incidents,
                                road_names,
                                route["geometry"],
                            )
                        )

                    except requests.RequestException:
                        st.warning(
                            "Unable to search for route "
                            "incidents at this time."
                        )
                        route_incidents = []

                    except Exception as error:
                        st.warning(
                            "Route incident analysis "
                            "could not be completed."
                        )
                        route_incidents = []

                # --------------------------------------------------
                # WEATHER
                # --------------------------------------------------

                with st.spinner(
                    "Getting current weather..."
                ):

                    try:

                        weather = get_weather(
                            origin["latitude"],
                            origin["longitude"],
                        )

                    except requests.RequestException:
                        st.warning(
                            "Unable to retrieve "
                            "current weather."
                        )
                        weather = None

                    except Exception:
                        st.warning(
                            "Weather information could "
                            "not be retrieved."
                        )
                        weather = None

                # --------------------------------------------------
                # SAVE RESULTS IN SESSION STATE
                # --------------------------------------------------

                st.session_state.route_data = {
                    "origin": origin,
                    "destination": destination_data,
                    "route": route,
                    "road_names": road_names,
                    "incidents": route_incidents,
                    "weather": weather,
                }

                st.session_state.route_planned = True


# ==================================================
# DISPLAY SAVED RESULTS
# ==================================================

if (
    st.session_state.route_planned
    and st.session_state.route_data
):

    data = st.session_state.route_data

    origin = data["origin"]
    destination_data = data["destination"]
    route = data["route"]
    road_names = data["road_names"]
    route_incidents = data["incidents"]
    weather = data["weather"]


    # --------------------------------------------------
    # ROUTE SUMMARY
    # --------------------------------------------------

    st.divider()

    st.subheader("🧭 Route Summary")

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "🛣️ Distance",
            f"{route['distance_km']:.1f} km",
        )

    with col2:
        st.metric(
            "⏱️ Estimated Time",
            f"{route['duration_minutes']:.0f} min",
        )


    # --------------------------------------------------
    # ROUTE ROADS
    # --------------------------------------------------

    st.subheader("🛣️ Route Roads")

    if road_names:

        for road in road_names:
            st.write(f"• {road}")

    else:

        st.info(
            "No named roads were found for this route."
        )


    # --------------------------------------------------
    # ROUTE MAP
    # --------------------------------------------------

    st.subheader("🗺️ Route Map")

    display_route_map(
        origin,
        destination_data,
        route,
    )


    # --------------------------------------------------
    # ROUTE ALERTS
    # --------------------------------------------------

    st.subheader("⚠️ Route Alerts")

    if route_incidents:

        st.warning(
            f"{len(route_incidents)} "
            f"potential route incident(s) found."
        )

        for incident in route_incidents:

            road = incident.get(
                "road",
                "Unknown road",
            )

            incident_type = incident.get(
                "type",
                "ROUTE ALERT",
            )

            with st.expander(
                f"🚨 {incident_type} — {road}"
            ):

                st.write(
                    f"**Incident:** "
                    f"{incident.get('title', 'N/A')}"
                )

                st.write(
                    f"**Freshness:** "
                    f"{incident.get('freshness', 'UNKNOWN')}"
                )

                st.write(
                    f"**Confidence:** "
                    f"{incident.get('confidence', 'UNKNOWN')}"
                )

                # Geographic distance from route
                if (
                    incident.get("route_distance_km")
                    is not None
                ):

                    st.write(
                        f"**Distance from route:** "
                        f"{incident['route_distance_km']:.1f} km"
                    )

                # Approximate reported location
                if incident.get("incident_location"):

                    st.write(
                        f"**Reported location:** "
                        f"{incident['incident_location']} "
                        f"(approximate)"
                    )

                st.write(
                    f"**Source:** "
                    f"{incident.get('source', 'N/A')}"
                )

                if incident.get("url"):

                    st.write(
                        f"[Read source]"
                        f"({incident['url']})"
                    )

    else:

        st.success(
            "✅ No relevant recent route "
            "incidents were found."
        )


    # --------------------------------------------------
    # WEATHER
    # --------------------------------------------------

    st.subheader(
        "🌤️ Current Weather at Starting Location"
    )

    if weather:

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Temperature",
                f"{weather['temperature']:.1f} °C",
            )

        with col2:
            st.metric(
                "Humidity",
                f"{weather['humidity']} %",
            )

        with col3:
            st.metric(
                "Condition",
                weather["description"],
            )

        with col4:
            st.metric(
                "Wind Speed",
                f"{weather['wind_speed']} km/h",
            )

    else:

        st.info(
            "Weather information is not available."
        )


    # --------------------------------------------------
    # TRAVEL BRIEF
    # --------------------------------------------------

    st.subheader("📋 Travel Brief")

    with st.container(border=True):

        travel_brief = generate_travel_brief(
            route,
            weather,
            route_incidents,
        )

        for item in travel_brief:
            st.write(item)


    st.caption(
        "⚠️ RouteGuard alerts are based on available "
        "public information and may not represent "
        "real-time road conditions. Always follow "
        "official traffic instructions and road signs."
    )


    # --------------------------------------------------
    # CURRENT LOCATION DETAILS
    # --------------------------------------------------

    st.subheader("📍 Current Location")

    st.write(
        origin["display_name"]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Latitude",
            f"{origin['latitude']:.6f}",
        )

    with col2:
        st.metric(
            "Longitude",
            f"{origin['longitude']:.6f}",
        )


    # --------------------------------------------------
    # DESTINATION DETAILS
    # --------------------------------------------------

    st.subheader("🏁 Destination")

    st.write(
        destination_data["display_name"]
    )

    col1, col2 = st.columns(2)

    with col1:
        st.metric(
            "Latitude",
            f"{destination_data['latitude']:.6f}",
        )

    with col2:
        st.metric(
            "Longitude",
            f"{destination_data['longitude']:.6f}",
        )
