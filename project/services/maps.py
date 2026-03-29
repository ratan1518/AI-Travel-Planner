from geopy.exc import GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable
from geopy.geocoders import Nominatim
import pandas as pd


def get_location_frame(destination: str) -> pd.DataFrame | None:
    try:
        geolocator = Nominatim(user_agent="travel_app", timeout=10)
        location = geolocator.geocode(destination)
    except (GeocoderServiceError, GeocoderTimedOut, GeocoderUnavailable, ValueError):
        return None

    if not location:
        return None

    return pd.DataFrame({"lat": [location.latitude], "lon": [location.longitude]})
