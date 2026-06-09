from geopy.exc import GeocoderRateLimited, GeocoderUnavailable
from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim

_geolocator = Nominatim(user_agent="roteirizador-academico-uff/1.0 (luan_carvalho@id.uff.br)", timeout=10)
_geocode = RateLimiter(_geolocator.geocode, min_delay_seconds=2.0, max_retries=1, error_wait_seconds=10.0)


class GeocodingRateLimitError(Exception):
    pass


def geocodificar(endereco: str) -> tuple[float, float] | None:
    try:
        loc = _geocode(endereco)
        if loc is None:
            return None
        return (loc.latitude, loc.longitude)
    except GeocoderRateLimited as exc:
        raise GeocodingRateLimitError(
            "Nominatim retornou erro 429 (rate limit). "
            "O IP do Streamlit Cloud esta temporariamente bloqueado. "
            "Aguarde alguns minutos e tente novamente."
        ) from exc
    except (GeocoderUnavailable, Exception):
        return None


def geocodificar_lote(enderecos: list[str]) -> list[tuple[float, float] | None]:
    return [geocodificar(e) for e in enderecos]
