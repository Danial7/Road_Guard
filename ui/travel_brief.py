def generate_travel_brief(
    route,
    weather,
    incidents,
):
    """
    Generate a simple human-readable travel brief.
    """

    distance = route["distance_km"]
    duration = route["duration_minutes"]

    brief = []

    # Route information
    brief.append(
        f"Your planned journey is approximately "
        f"{distance:.1f} km with an estimated driving "
        f"time of {duration:.0f} minutes."
    )

    # Incident information
    if incidents:

        high_confidence = [
            incident
            for incident in incidents
            if incident["confidence"] == "HIGH"
        ]

        recent_incidents = [
            incident
            for incident in incidents
            if incident["freshness"]
            in ["VERY_RECENT", "RECENT"]
        ]

        if high_confidence:

            brief.append(
                "⚠️ Caution is advised. Recent reports "
                "indicate potential disruption on one or "
                "more roads included in your route."
            )

        elif recent_incidents:

            brief.append(
                "⚠️ Be prepared for possible disruption "
                "or delays near affected sections of "
                "your route."
            )

        else:

            brief.append(
                "ℹ️ Some older reports were found on "
                "roads included in your route."
            )

    else:

        brief.append(
            "✅ No relevant recent public reports "
            "were found for the selected route."
        )

    # Weather information
    if weather:

        brief.append(
            f"🌤️ Current conditions are "
            f"{weather['description'].lower()} "
            f"with a temperature of "
            f"{weather['temperature']:.1f}°C."
        )

    # Overall recommendation
    if incidents:

        brief.append(
            "Overall: Exercise caution and allow "
            "some flexibility in your travel time."
        )

    else:

        brief.append(
            "Overall: No significant route-related "
            "alerts were identified from the available "
            "public information."
        )

    return brief
