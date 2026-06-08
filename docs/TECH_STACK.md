# TECH_STACK — Roteirizador

> Bibliotecas, serviços gratuitos e seus limites. Tudo Python, custo zero, sem chaves de API.

---

## 1. requirements.txt (proposto)

```
streamlit
streamlit-folium
folium
geopy
requests
pandas
openpyxl            # leitura dos .xlsx de referência em Trabalho_final/
VRPSolverEasy
```

> Verifique as versões instaladas no ambiente antes de fixar. O VRPSolverEasy já está instalado e
> funcionando (o notebook em `../Trabalho_final/` roda). Use a documentação via Context7/MCP se
> precisar confirmar assinaturas atuais de qualquer biblioteca.

## 2. Geocoding — Nominatim via geopy

Converte endereço em coordenadas, **grátis e sem chave**.

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(user_agent="roteirizador-academico-uff")  # User-Agent obrigatório
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1.0) # respeita a política de uso

loc = geocode("Rua da Conceição, 29, Centro, Niterói - RJ")
if loc:
    lat, lon = loc.latitude, loc.longitude
```

**Política de uso do Nominatim (servidor público — respeitar):**
- Máximo **1 requisição por segundo** (use `RateLimiter`).
- **User-Agent identificável obrigatório** (não use o padrão).
- Não é para uso pesado/produção. Para uma dezena de endereços por cenário, está perfeito.
- Dica: acrescentar ", Brasil" ou o estado ao endereço melhora a taxa de acerto.

## 3. Distância e geometria — OSRM (servidor público)

Servidor de demonstração: `https://router.project-osrm.org`. **Grátis, sem chave.**

### Matriz de distância (`/table`)

```
GET /table/v1/driving/{lon1},{lat1};{lon2},{lat2};...?annotations=distance
```

- **Ordem das coordenadas é `lon,lat`** (longitude primeiro) — erro comum, atenção.
- `annotations=distance` retorna a matriz em **metros** (`distances`). Sem isso, vem só duração.
- Converta metros → km dividindo por 1000 (o solver e o resto do app trabalham em km).
- A matriz pode ser **assimétrica** (ida ≠ volta) — o modelo usa links direcionados, ok.

### Geometria da rota para o mapa (`/route`)

```
GET /route/v1/driving/{coords}?overview=full&geometries=geojson
```

- Passe a **sequência ordenada** dos pontos de uma rota; recebe a polilinha do trajeto completo.
- `geometries=geojson` → `routes[0].geometry.coordinates` é uma lista de `[lon, lat]`.
  **Inverta para `(lat, lon)`** antes de passar ao Folium.

**Limites do servidor público OSRM:**
- Uso "razoável" apenas; não garantido para produção; pode ter rate limit.
- `/table` na demo costuma limitar o nº de coordenadas (ordem de ~100) — suficiente para o MVP.
- Plano B se o público falhar/limitar: subir OSRM local via Docker (`osrm-backend`) com um
  `.osm.pbf` da região (ex.: Sudeste do Brasil pelo Geofabrik). **Fora do escopo do MVP**, mas
  registre como caminho de evolução. Trate indisponibilidade como erro amigável (ver ARCHITECTURE §5).

## 4. Solver — VRPSolverEasy

Solver exato (Branch-Cut-and-Price) acadêmico. Usa o solver linear **CLP** (gratuito).
**É um requisito do trabalho — não substituir.** Detalhes de API em `REFERENCE.md`.

- Já está instalado e funcional no ambiente (o notebook resolve a instância de Niterói).
- A licença acadêmica já está configurada **localmente**. Como o MVP roda em localhost, **não há
  problema de licença a resolver** (o problema de licença era só para deploy em nuvem, que está
  fora do escopo).

## 5. Mapa — Folium + streamlit-folium

Gera um mapa Leaflet/OpenStreetMap **sem escrever JS**.

```python
import folium
from streamlit_folium import st_folium

m = folium.Map(location=[lat_centro, lon_centro], zoom_start=13)
folium.Marker([lat, lon], tooltip="Depósito D1",
              icon=folium.Icon(color="black")).add_to(m)
folium.PolyLine(coords_da_rota, color="#c0392b", weight=4).add_to(m)  # coords = [(lat,lon), ...]

st_folium(m, width=800, height=500)   # renderiza no Streamlit
```

- Use uma **paleta de cores distintas** para as rotas (uma cor por rota).
- Marcadores diferentes para depósitos vs clientes (cor/ícone).
- `PolyLine` recebe a geometria real vinda do OSRM (não ligue os pontos em linha reta).

## 6. Resumo das fontes externas e o que pode falhar

| Serviço | Uso | Chave? | Principal limite | Fallback |
|---|---|---|---|---|
| Nominatim | geocoding | não | 1 req/s, User-Agent | mensagem de erro + correção manual |
| OSRM demo | matriz + geometria | não | uso razoável, ~100 coords | OSRM local via Docker (pós-MVP) |
| VRPSolverEasy | solver | licença local já ok | tamanho da instância | mostrar status "inviável"/"erro" |
