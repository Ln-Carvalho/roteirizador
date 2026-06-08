# Roteirizador — Otimizador de Rotas (CVRP) com Interface Web

Uma aplicação web desenvolvida 100% em Python para resolver o **Problema de Roteamento de Veículos com Capacidade (CVRP)**. O sistema suporta **múltiplos depósitos**, **frota heterogênea** e **múltiplas viagens por veículo**, utilizando o poderoso solver acadêmico **VRPSolverEasy** para encontrar soluções exatas ou de alta qualidade.

O projeto foi desenvolvido para a disciplina de Tópicos I (Roteamento de Veículos) e possui uma interface amigável construída com Streamlit, que exibe as rotas otimizadas diretamente em um mapa interativo. O sistema não depende de APIs pagas, utilizando serviços gratuitos baseados em OpenStreetMap para geocodificação e cálculo de distâncias.

---

## 🎯 Funcionalidades Principais

- **Gestão de Endereços:** Entrada facilitada de pontos de entrega e definição de demandas. Permite selecionar quais pontos atuarão como depósitos (pontos de origem/destino sem demanda própria).
- **Configuração da Frota:** Cadastro de veículos com capacidades, quantidades e custos por km distintos. É possível associar veículos a depósitos específicos e configurar se os mesmos devem retornar ao depósito ao final da rota.
- **Restrições Avançadas:** Suporte a múltiplas viagens pelo mesmo veículo e validações de segurança para garantir que a demanda total possa ser atendida pela frota disponível.
- **Visualização e Resultados:** Mapas interativos gerados via Folium, desenhando as rotas reais pelas vias (via OSRM). Apresentação do custo total, tempo de solução e taxa de ocupação por rota.

---

## 🛠️ Tecnologias Utilizadas

| Componente | Tecnologia |
|---|---|
| **Interface Web** | [Streamlit](https://streamlit.io/) |
| **Geocodificação** (Endereços → Lat/Lon) | Nominatim via `geopy` |
| **Roteamento e Matriz de Distâncias** | [OSRM](http://project-osrm.org/) (OpenStreetMap) |
| **Solver de Otimização** | [VRPSolverEasy](https://vrpsolver.math.u-bordeaux.fr/) |
| **Mapas Interativos** | Folium + `streamlit-folium` |

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.10 ou superior
- Recomenda-se o uso de um ambiente virtual (`venv` ou `conda`)

### Passos de Instalação

1. Clone o repositório:
```bash
git clone https://github.com/Ln-Carvalho/roteirizador.git
cd roteirizador
```

2. Instale as dependências necessárias:
```bash
pip install -r requirements.txt
```

3. Inicie a aplicação:
```bash
streamlit run app.py
```

4. A interface estará disponível no seu navegador em: `http://localhost:8501`.

---

## 🎓 Créditos e Agradecimentos

Este projeto foi desenvolvido por **Luan Carvalho** para a disciplina de **Tópicos em Engenharia de Produção da UFF - TEP00132**, ministrada pelo **Professor Eduardo Uchoa**.

Um agradecimento especial aos desenvolvedores da biblioteca **VRPSolverEasy** por fornecer uma interface acessível e robusta para a modelagem matemática de problemas de roteamento, o que viabilizou as soluções exatas neste trabalho.
