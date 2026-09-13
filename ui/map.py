import folium
from streamlit_folium import st_folium


def display_route_map(origin, destination, route):
    """
    Display the calculated route on an interactive map.
    """

    origin_location = [
        origin["latitude"],
        origin["longitude"],
    ]

    destination_location = [
        destination["latitude"],
        destination["longitude"],
    ]

    # Create map centered between origin and destination
    route_map = folium.Map(
        location=origin_location,
        zoom_start=11,
    )

    # Start marker
    folium.Marker(
        origin_location,
        tooltip="Current Location",
        popup=origin["display_name"],
        icon=folium.Icon(
            color="green",
            icon="play",
        ),
    ).add_to(route_map)

    # Destination marker
    folium.Marker(
        destination_location,
        tooltip="Destination",
        popup=destination["display_name"],
        icon=folium.Icon(
            color="red",
            icon="flag",
        ),
    ).add_to(route_map)

    # Extract route coordinates from GeoJSON
    coordinates = route["geometry"]["coordinates"]

    # GeoJSON uses longitude, latitude
    route_points = [
        [coordinate[1], coordinate[0]]
        for coordinate in coordinates
    ]

    # Draw route
    folium.PolyLine(
        route_points,
        weight=6,
        opacity=0.8,
        tooltip="RouteGuard Recommended Route",
    ).add_to(route_map)

    # Automatically fit map to route
    route_map.fit_bounds(
        [
            origin_location,
            destination_location,
        ]
    )

    # Display map in Streamlit
    st_folium(
        route_map,
        width=None,
        height=500,
    )
