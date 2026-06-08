import requests

OSRM_BASE = "https://router.project-osrm.org"


def geometria_rota(coords_ordenadas: list[tuple[float, float]]) -> list[tuple[float, float]]:
    """
    Dado a sequência ordenada de (lat, lon) de uma rota, retorna a polilinha
    real das ruas via OSRM /route?overview=full&geometries=geojson.
    Retorna lista de (lat, lon). Em caso de erro ou entrada insuficiente,
    retorna lista vazia (nunca lança exceção).
    """
    if len(coords_ordenadas) < 2:
        return []

    # OSRM espera lon,lat
    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coords_ordenadas)
    url = (
        f"{OSRM_BASE}/route/v1/driving/{coords_str}"
        "?overview=full&geometries=geojson"
    )

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException:
        return []

    if data.get("code") != "Ok" or not data.get("routes"):
        return []

    # GeoJSON coordinates são [lon, lat] → inverter para (lat, lon)
    geojson_coords = data["routes"][0]["geometry"]["coordinates"]
    return [(lat, lon) for lon, lat in geojson_coords]
