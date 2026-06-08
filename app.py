import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

from core.distance import matriz_distancias
from core.geocoding import geocodificar_lote
from core.mapa import desenhar
from core.models import Cenario, Ponto, TipoVeiculo
from core.routing_geometry import geometria_rota
from core.solver import resolver

st.set_page_config(page_title="Roteirizador CVRP", layout="wide")


def _init_state():
    defaults = {
        "etapa": 1,
        "pontos": [],
        "veiculos": [],
        "retornar_ao_deposito": True,
        "permitir_multiplas_viagens": False,
        "solucao": None,
        "geometrias": {},
        "df_enderecos": pd.DataFrame({
            "endereco": ["", "", ""],
            "demanda": [0, 100, 80],
            "deposito": [True, False, False],
        }),
        "df_frota": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


def _barra_progresso():
    with st.sidebar:
        st.markdown("### Roteirizador CVRP")
        st.caption("Desenvolvido por **Luan Carvalho** para a disciplina de **Tópicos em Engenharia de Produção da UFF - TEP00132** (Prof. Eduardo Uchoa).")
        st.caption("Agradecimentos à biblioteca **VRPSolverEasy** pelo desenvolvimento da biblioteca.")
        
    etapa = st.session_state.etapa
    cols = st.columns(3)
    rotulos = ["1. Enderecos", "2. Frota", "3. Resultado"]
    for i, (col, rotulo) in enumerate(zip(cols, rotulos)):
        if i + 1 == etapa:
            col.markdown(f"**{rotulo}**")
        else:
            col.markdown(rotulo)


_barra_progresso()
st.divider()


def _etapa_1():
    st.header("Etapa 1: Enderecos")
    st.caption(
        "Informe os pontos de entrega. "
        "Marque 'Deposito' em ao menos um ponto. "
        "Clientes devem ter demanda > 0. "
        "Use o '+' no fim da tabela para adicionar pontos."
    )
    st.caption(
        "Exemplo de endereco: 'Rua da Conceicao 100, Centro, Niteroi, RJ'. "
        "Quanto mais completo (rua, numero, bairro, cidade, estado), melhor a geocodificacao."
    )

    df_editado = st.data_editor(
        st.session_state.df_enderecos,
        num_rows="dynamic",
        column_config={
            "endereco": st.column_config.TextColumn(
                "Endereco", width="large",
                help="Rua, numero, bairro, cidade e estado. Ex.: Rua da Conceicao 100, Centro, Niteroi, RJ",
            ),
            "demanda": st.column_config.NumberColumn(
                "Demanda", min_value=0, step=1, format="%d",
                help="Quantidade a entregar no cliente, em numero inteiro (ex.: caixas, pacotes). "
                     "Depositos podem ficar com 0.",
            ),
            "deposito": st.column_config.CheckboxColumn(
                "Deposito", help="Marque para usar este ponto como deposito (origem dos veiculos).",
            ),
        },
        use_container_width=True,
        key="editor_enderecos",
    )
    # A base passada ao editor permanece estavel entre reruns; o estado de edicao
    # (incluindo linhas adicionadas) vive no delta keyed. Reescrever a base aqui
    # dessincroniza esse delta e faz a linha nova exigir duplo preenchimento.
    # Por isso higienizamos uma COPIA e so persistimos a base ao navegar.
    df = df_editado.copy()
    df["endereco"] = df["endereco"].fillna("").astype(str)
    df["deposito"] = df["deposito"].fillna(False).astype(bool)
    df["demanda"] = pd.to_numeric(df["demanda"], errors="coerce").fillna(0).astype(int)

    validos = df[df["endereco"].str.strip() != ""]
    tem_deposito = bool(validos["deposito"].any())
    tem_cliente = bool((~validos["deposito"] & (validos["demanda"] > 0)).any())

    if not tem_deposito:
        st.warning("Marque ao menos um ponto como deposito.")
    if not tem_cliente:
        st.warning("Adicione ao menos um cliente com demanda > 0.")

    pode_avancar = tem_deposito and tem_cliente and len(validos) >= 2

    if st.button("Geocodificar e Avancar", disabled=not pode_avancar, type="primary"):
        st.session_state.pontos = []   # limpa estado anterior antes de tentar
        enderecos = validos["endereco"].tolist()
        with st.spinner("Geocodificando enderecos (1 s por endereco)..."):
            coords = geocodificar_lote(enderecos)

        falhas = [e for e, c in zip(enderecos, coords) if c is None]
        if falhas:
            for f in falhas:
                st.error(f"Endereco nao encontrado: {f}")
            return

        pontos = []
        for idx, (_, row) in enumerate(validos.iterrows()):
            lat, lon = coords[idx]
            pontos.append(Ponto(
                id=idx,
                endereco=str(row["endereco"]),
                lat=lat,
                lon=lon,
                is_deposito=bool(row["deposito"]),
                demanda=0 if bool(row["deposito"]) else int(row["demanda"]),
            ))

        st.session_state.pontos = pontos
        st.session_state.df_enderecos = df   # snapshot p/ preservar ao voltar
        st.session_state.df_frota = None
        st.session_state.etapa = 2
        st.rerun()


def _etapa_2():
    st.header("Etapa 2: Frota")
    pontos = st.session_state.pontos
    depositos = [p for p in pontos if p.is_deposito]
    opcoes_deposito = [p.endereco for p in depositos]
    demanda_total = sum(p.demanda for p in pontos if not p.is_deposito)

    st.caption(f"Demanda total dos clientes: {demanda_total:.0f} unidades")

    if st.session_state.df_frota is None:
        st.session_state.df_frota = pd.DataFrame({
            "tipo": ["Van"],
            "capacidade": [500],
            "quantidade": [2],
            "custo_por_km": [1.0],
            "deposito": [opcoes_deposito[0] if opcoes_deposito else ""],
        })

    df_frota = st.data_editor(
        st.session_state.df_frota,
        num_rows="dynamic",
        column_config={
            "tipo": st.column_config.TextColumn("Tipo", width="small"),
            "capacidade": st.column_config.NumberColumn(
                "Capacidade", min_value=1, step=50, format="%d",
                help="Capacidade de carga do veiculo, em numero inteiro (mesma unidade da demanda).",
            ),
            "quantidade": st.column_config.NumberColumn(
                "Qtd", min_value=1, step=1, format="%d",
                help="Quantos veiculos deste tipo estao disponiveis.",
            ),
            "custo_por_km": st.column_config.NumberColumn("Custo/km", min_value=0.0, step=0.1),
            "deposito": st.column_config.SelectboxColumn(
                "Deposito de origem", options=opcoes_deposito
            ),
        },
        use_container_width=True,
        key="editor_frota",
    )
    # Base estavel + key: higieniza uma COPIA, nao reescreve a base no render
    # (mesmo motivo da Etapa 1; evita a linha nova exigir duplo preenchimento).
    dff = df_frota.copy()
    dff["capacidade"] = pd.to_numeric(dff["capacidade"], errors="coerce")
    dff["quantidade"] = pd.to_numeric(dff["quantidade"], errors="coerce")
    dff["custo_por_km"] = pd.to_numeric(dff["custo_por_km"], errors="coerce").fillna(0.0)

    retornar = st.toggle(
        "Veiculos retornam ao deposito de origem",
        value=st.session_state.retornar_ao_deposito,
    )
    st.session_state.retornar_ao_deposito = retornar

    multiplas_viagens = st.toggle(
        "Permitir multiplas viagens por veiculo",
        value=st.session_state.get("permitir_multiplas_viagens", False),
        help="Se marcado, a demanda total pode ultrapassar a frota física e o solver criará múltiplas rotas para o mesmo tipo de veículo.",
    )
    st.session_state.permitir_multiplas_viagens = multiplas_viagens

    df_frota_valido = dff.dropna(subset=["capacidade", "quantidade"])
    cap_total = float((df_frota_valido["capacidade"] * df_frota_valido["quantidade"]).sum())
    max_cap_veiculo = float(df_frota_valido["capacidade"].max()) if not df_frota_valido.empty else 0.0
    max_demanda_ponto = max([p.demanda for p in pontos if not p.is_deposito], default=0.0)
    
    demanda_ponto_ok = max_cap_veiculo >= max_demanda_ponto
    frota_ok = (cap_total >= demanda_total or multiplas_viagens) and demanda_ponto_ok

    if not demanda_ponto_ok:
        st.error(
            f"Inviavel: Existe um cliente com demanda ({max_demanda_ponto:.0f}) maior que a capacidade do maior veiculo ({max_cap_veiculo:.0f}). "
            "O modelo atual nao permite dividir a entrega de um mesmo cliente em multiplos veiculos."
        )
    elif not (cap_total >= demanda_total or multiplas_viagens):
        st.error(
            f"Frota insuficiente: demanda total {demanda_total:.0f} > capacidade total {cap_total:.0f}"
        )
    elif cap_total < demanda_total and multiplas_viagens:
        st.warning(f"Capacidade total fisica ({cap_total:.0f}) menor que demanda ({demanda_total:.0f}), mas permitindo multiplas viagens.")
    else:
        st.success(f"Capacidade total: {cap_total:.0f}  |  Demanda: {demanda_total:.0f}")

    col_v, col_c = st.columns([1, 5])
    with col_v:
        if st.button("Voltar"):
            st.session_state.df_frota = dff   # snapshot p/ preservar a frota
            st.session_state.etapa = 1
            st.rerun()
    with col_c:
        if st.button("Calcular Rota", disabled=not frota_ok, type="primary"):
            st.session_state.df_frota = dff   # snapshot p/ preservar a frota
            dep_por_endereco = {p.endereco: p.id for p in depositos}
            veiculos = []
            for idx, (_, row) in enumerate(dff.iterrows()):
                if pd.isna(row.get("capacidade")) or pd.isna(row.get("quantidade")):
                    continue
                dep_id = dep_por_endereco.get(str(row["deposito"]), depositos[0].id)
                veiculos.append(TipoVeiculo(
                    id=idx + 1,
                    nome=str(row["tipo"]),
                    capacidade=int(round(float(row["capacidade"]))),
                    quantidade=int(row["quantidade"]),
                    custo_por_km=float(row["custo_por_km"]),
                    deposito_id=dep_id,
                ))
            st.session_state.veiculos = veiculos
            st.session_state.solucao = None
            st.session_state.etapa = 3
            st.rerun()


def _etapa_3():
    st.header("Etapa 3: Resultado")
    pontos = st.session_state.pontos
    veiculos = st.session_state.veiculos

    if not pontos or not veiculos:
        st.warning("Estado invalido. Retornando ao inicio.")
        st.session_state.etapa = 1
        st.rerun()
        return

    if st.session_state.solucao is None:
        cenario = Cenario(
            pontos=pontos,
            veiculos=veiculos,
            retornar_ao_deposito=st.session_state.retornar_ao_deposito,
            permitir_multiplas_viagens=st.session_state.get("permitir_multiplas_viagens", False),
        )
        with st.spinner("Calculando matriz de distancias (OSRM)..."):
            try:
                coords = [(p.lat, p.lon) for p in pontos]
                matriz = matriz_distancias(coords)
            except RuntimeError as exc:
                st.error(f"Servico de rotas indisponivel: {exc}")
                return

        with st.spinner("Resolvendo CVRP (VRPSolverEasy)..."):
            sol = resolver(cenario, matriz)
        st.session_state.solucao = sol

        if sol.status == "otimo":
            with st.spinner("Obtendo geometria das rotas (OSRM)..."):
                id_to_coord = {p.id: (p.lat, p.lon) for p in pontos}
                geoms: dict[int, list[tuple[float, float]]] = {}
                for k, rota in enumerate(sol.rotas):
                    seq_coords = [
                        id_to_coord[pid]
                        for pid in rota.sequencia_ids
                        if pid in id_to_coord
                    ]
                    geoms[k] = geometria_rota(seq_coords)
            st.session_state.geometrias = geoms

    sol = st.session_state.solucao

    if sol.status != "otimo":
        msg = "Solucao inviavel" if sol.status == "inviavel" else "Erro no solver"
        st.error(f"{msg}: {sol.mensagem}")
        if st.button("Voltar e ajustar"):
            st.session_state.etapa = 2
            st.rerun()
        return

    col_mapa, col_resumo = st.columns([3, 1])

    with col_resumo:
        st.subheader("Resumo")
        st.metric("Custo total", f"R$ {sol.custo_total:.2f}")
        st.metric("Tempo solver", f"{sol.tempo_solucao:.2f} s")
        st.metric("Rotas geradas", len(sol.rotas))
        st.caption(sol.mensagem)
        st.divider()
        id_to_endereco = {p.id: p.endereco for p in pontos}
        for k, rota in enumerate(sol.rotas):
            seq_enderecos = " ➔ ".join([id_to_endereco.get(pid, str(pid)) for pid in rota.sequencia_ids])
            st.markdown(
                f"**Rota {k + 1}** — {rota.veiculo_tipo}  \n"
                f"Deposito: {id_to_endereco.get(rota.deposito_id, rota.deposito_id)}  \n"
                f"Carga: {rota.carga_usada:.0f} / {rota.capacidade:.0f}  \n"
                f"Distancia: {rota.distancia:.1f} km  \n"
                f"**Sequencia:** {seq_enderecos}"
            )

    with col_mapa:
        mapa = desenhar(sol, pontos, st.session_state.geometrias)
        st_folium(mapa, width=800, height=550, returned_objects=[])

    if st.button("Voltar e recalcular"):
        st.session_state.solucao = None
        st.session_state.etapa = 2
        st.rerun()


if st.session_state.etapa == 1:
    _etapa_1()
elif st.session_state.etapa == 2:
    _etapa_2()
elif st.session_state.etapa == 3:
    _etapa_3()
