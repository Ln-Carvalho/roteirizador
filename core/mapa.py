import folium
from core.models import Ponto, Solucao

_PALETA = [
    "#c0392b", "#2980b9", "#27ae60", "#8e44ad", "#e67e22",
    "#16a085", "#d35400", "#2c3e50", "#f39c12", "#1abc9c",
]


def desenhar(
    solucao: Solucao,
    pontos: list[Ponto],
    geometrias: dict[int, list[tuple[float, float]]],
) -> folium.Map:
    """
    geometrias: índice da rota (0-based) → lista de (lat, lon) seguindo as ruas.
    """
    lats = [p.lat for p in pontos if p.lat is not None]
    lons = [p.lon for p in pontos if p.lon is not None]
    centro = (
        (sum(lats) / len(lats), sum(lons) / len(lons))
        if lats else (-22.9, -43.1)
    )

    m = folium.Map(location=centro, zoom_start=13)

    for p in pontos:
        if p.lat is None or p.lon is None:
            continue
        if p.is_deposito:
            folium.Marker(
                location=[p.lat, p.lon],
                tooltip=f"Deposito: {p.endereco}",
                icon=folium.Icon(color="black", icon="home"),
            ).add_to(m)
        else:
            folium.Marker(
                location=[p.lat, p.lon],
                tooltip=f"Cliente {p.id}: {p.endereco} (demanda={p.demanda:.0f})",
                icon=folium.Icon(color="blue", icon="info-sign"),
            ).add_to(m)

    for k, rota in enumerate(solucao.rotas):
        cor = _PALETA[k % len(_PALETA)]
        poly = geometrias.get(k)
        if poly:
            folium.PolyLine(
                locations=poly,
                color=cor,
                weight=4,
                tooltip=(
                    f"Rota {k + 1} | {rota.veiculo_tipo} | "
                    f"Carga: {rota.carga_usada:.0f}/{rota.capacidade:.0f} | "
                    f"Dist: {rota.distancia:.1f} km"
                ),
            ).add_to(m)

    return m
