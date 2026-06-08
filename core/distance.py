import requests

OSRM_BASE = "https://router.project-osrm.org"


def matriz_distancias(coords: list[tuple[float, float]]) -> list[list[float]]:
    """
    Retorna matriz NxN de distâncias reais em km via OSRM /table.
    coords: lista de (lat, lon). OSRM espera lon,lat — inversão feita aqui.
    Lança RuntimeError se o serviço estiver indisponível.
    """
    if not coords:
        return []

    coords_str = ";".join(f"{lon},{lat}" for lat, lon in coords)
    url = f"{OSRM_BASE}/table/v1/driving/{coords_str}?annotations=distance"

    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        raise RuntimeError(f"OSRM indisponivel: {exc}") from exc

    if data.get("code") != "Ok":
        raise RuntimeError(f"OSRM retornou erro: {data.get('message', data.get('code'))}")

    # 'distances' vem em metros → converter para km
    metros = data["distances"]
    return [[m / 1000.0 for m in linha] for linha in metros]
