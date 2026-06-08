import time
import VRPSolverEasy as vre
from core.models import Cenario, Rota, Solucao


def resolver(cenario: Cenario, matriz_dist: list[list[float]]) -> Solucao:
    """
    Constrói e resolve o modelo VRPSolverEasy.
    Retorna Solucao com status "otimo", "inviavel" ou "erro".
    matriz_dist: NxN em km, indexado pela posição em cenario.pontos.
    """
    try:
        return _resolver_interno(cenario, matriz_dist)
    except Exception as exc:
        return Solucao(
            rotas=[], custo_total=0.0, tempo_solucao=0.0,
            status="erro", mensagem=str(exc),
        )


def _resolver_interno(cenario: Cenario, matriz_dist: list[list[float]]) -> Solucao:
    model = vre.Model()

    tipo_por_id = {v.id: v for v in cenario.veiculos}

    # Tipos de veículo
    for v in cenario.veiculos:
        end_pt = v.deposito_id if cenario.retornar_ao_deposito else -1
        max_rotas = v.quantidade * 50 if getattr(cenario, 'permitir_multiplas_viagens', False) else v.quantidade
        model.add_vehicle_type(
            id=v.id,
            start_point_id=v.deposito_id,
            end_point_id=end_pt,
            capacity=int(round(v.capacidade)),  # VRPSolverEasy exige inteiro
            max_number=max_rotas,
            var_cost_dist=v.custo_por_km,
        )

    # Depósitos
    for p in cenario.pontos:
        if p.is_deposito:
            model.add_depot(id=p.id)

    # Clientes
    for p in cenario.pontos:
        if not p.is_deposito:
            model.add_customer(id=p.id, demand=int(round(p.demanda)))  # exige inteiro

    # Arcos (dígrafo — matriz pode ser assimétrica)
    for i, pi in enumerate(cenario.pontos):
        for j, pj in enumerate(cenario.pontos):
            if i != j:
                model.add_link(
                    start_point_id=pi.id,
                    end_point_id=pj.id,
                    distance=round(float(matriz_dist[i][j]), 3),
                    is_directed=True,
                )

    t0 = time.time()
    model.set_parameters(solver_name="CLP")
    model.solve()
    tempo = round(time.time() - t0, 3)

    # Use model.status (NOT sol.is_defined — that is a method, not a bool)
    if model.status != 0:
        return Solucao(
            rotas=[], custo_total=0.0, tempo_solucao=tempo,
            status="inviavel", mensagem=model.message,
        )

    sol = model.solution
    id_to_idx = {p.id: idx for idx, p in enumerate(cenario.pontos)}
    rotas: list[Rota] = []

    for route in sol.routes:
        tipo_id = route.vehicle_type_id
        tipo = tipo_por_id.get(tipo_id)
        nome_tipo = tipo.nome if tipo else f"tipo_{tipo_id}"
        dep_id = tipo.deposito_id if tipo else route.point_ids[0]
        carga = route.cap_consumption[-1] if route.cap_consumption else 0.0
        cap = tipo.capacidade if tipo else 0.0

        seq = list(route.point_ids)
        dist_rota = sum(
            matriz_dist[id_to_idx[seq[k]]][id_to_idx[seq[k + 1]]]
            for k in range(len(seq) - 1)
        )

        rotas.append(Rota(
            veiculo_tipo=nome_tipo,
            deposito_id=dep_id,
            sequencia_ids=seq,
            carga_usada=carga,
            capacidade=cap,
            distancia=round(dist_rota, 3),
        ))

    return Solucao(
        rotas=rotas,
        custo_total=sol.value,
        tempo_solucao=tempo,
        status="otimo",
        mensagem=model.message,
    )
