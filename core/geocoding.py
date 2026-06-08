from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

_geolocator = Nominatim(user_agent="roteirizador-academico-uff")
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=1.0)


def geocodificar(endereco: str) -> tuple[float, float] | None:
    try:
        loc = _geocode(endereco)
        if loc is None:
            return None
        return (loc.latitude, loc.longitude)
    except Exception:
        return None


def geocodificar_lote(enderecos: list[str]) -> list[tuple[float, float] | None]:
    return [geocodificar(e) for e in enderecos]
