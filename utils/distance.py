from math import radians, sin, cos, sqrt, atan2


def calculate_distance_km(
    latitude1,
    longitude1,
    latitude2,
    longitude2,
):
    earth_radius_km = 6371.0

    lat1 = radians(latitude1)
    lon1 = radians(longitude1)

    lat2 = radians(latitude2)
    lon2 = radians(longitude2)

    delta_lat = lat2 - lat1
    delta_lon = lon2 - lon1

    a = (
        sin(delta_lat / 2) ** 2
        + cos(lat1)
        * cos(lat2)
        * sin(delta_lon / 2) ** 2
    )

    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    return earth_radius_km * c


def distance_to_route_km(
    latitude,
    longitude,
    route_geometry,
):
    minimum_distance = None

    for coordinate in route_geometry["coordinates"]:
        route_longitude = coordinate[0]
        route_latitude = coordinate[1]

        distance = calculate_distance_km(
            latitude,
            longitude,
            route_latitude,
            route_longitude,
        )

        if (
            minimum_distance is None
            or distance < minimum_distance
        ):
            minimum_distance = distance

    return minimum_distance
