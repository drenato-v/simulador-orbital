# Arquitetura do Simulador Orbital

Este documento é o mapa do projeto: o que cada pasta e cada arquivo fazem, por onde os dados passam e quais regras garantem que os resultados sejam reproduzíveis.

---

## 1. Conceito

**Arquitetura de software** é a forma como um sistema se divide em partes, quais responsabilidades cada parte tem e como os dados passam entre elas.

Num projeto científico há uma exigência a mais: a **reprodutibilidade**. Qualquer pessoa deve conseguir refazer um cálculo e obter o mesmo número, sabendo exatamente de onde veio cada dado e com quais parâmetros ele foi processado.

### Os três princípios do projeto

1. **Separação de responsabilidades.** Quem busca dados não calcula física, e quem calcula física não desenha.
2. **Motor puro.** O código em C (`core/`) nunca acessa a rede. Ele recebe arquivos, calcula e escreve arquivos. Assim ele é determinístico (mesma entrada, mesma saída), testável e portátil, inclusive para o navegador via WebAssembly.
3. **Linhagem dos dados.** A resposta bruta da API é guardada intacta, e todo o resto é derivado dela por scripts. Se algo der errado, basta regenerar.

---

## 2. Fluxo de dados

```
JPL Horizons ──HTTP──▶ horizons.py ──▶ data/raw/          (bruto, imutável)
                                            │
                                      conversao.py
                                            ▼
                                  data/processed/ic_*.json
                                            │
                     config/*.json ──▶ core/apps/simular   (C, offline)
                                            ▼
                                  results/<execução>/*.csv
                                            │
       data/reference/*.csv ──▶ comparar_com_referencia.py ──▶ gráficos de erro
```

---

## 3. Árvore de pastas e arquivos

```
SimuladorOrbital/
├── README.md                     # visão geral, como executar, roadmap
├── .gitignore                    # o que o Git ignora (binários, results/, caches)
├── Makefile                      # compila o motor e roda os testes
│
├── docs/
│   ├── arquitetura.md            # este documento
│   ├── fisica.md                 # as equações do simulador
│   └── validacao.md              # métricas, experimentos e resultados
│
├── config/
│   └── simulacao_padrao.json     # parâmetros de uma execução
│
├── core/                         # motor físico em C
│   ├── include/orbital/          # interfaces públicas (.h)
│   │   ├── constantes.h
│   │   ├── vetor3.h
│   │   ├── corpo.h
│   │   ├── sistema.h
│   │   ├── forcas.h
│   │   ├── integradores.h
│   │   └── io.h
│   ├── src/                      # implementações (.c), uma para cada .h
│   ├── apps/
│   │   └── simular.c             # programa principal
│   ├── tests/
│   │   ├── test_vetor3.c
│   │   ├── test_orbita_circular.c
│   │   └── test_conservacao_energia.c
│   └── third_party/cJSON/        # biblioteca de terceiros, isolada
│
├── analysis/                     # Python
│   ├── requirements.txt
│   ├── orbital_data/             # pacote reutilizável
│   │   ├── __init__.py
│   │   ├── horizons.py           # ÚNICO módulo que acessa a API
│   │   ├── corpos.py             # tabela de corpos e seus IDs
│   │   └── conversao.py          # bruto → formato do projeto
│   ├── scripts/                  # programas executáveis
│   │   ├── baixar_condicoes_iniciais.py
│   │   ├── baixar_referencia.py
│   │   └── comparar_com_referencia.py
│   └── notebooks/                # explorações e figuras
│
├── data/
│   ├── raw/horizons/<época>/     # respostas da API como vieram
│   ├── processed/                # condições iniciais prontas para o C
│   └── reference/                # séries temporais de gabarito
│
├── results/                      # saídas das simulações (não versionadas)
├── web/                          # visualização 3D (futuro)
└── legacy/                       # primeira versão, a ser migrada
```

---

## 4. O que cada parte faz

### 4.1 `core/`: o motor físico (C)

| Arquivo | Responsabilidade |
|---|---|
| `constantes.h` | Unidades do projeto (UA, dia, UA³/dia²) e constantes, como a velocidade da luz em UA/dia |
| `vetor3.h` | Tipo `Vetor3` (x, y, z) e operações: soma, subtração, escala, produto escalar, norma |
| `corpo.h` | Tipo `Corpo`: id do Horizons, nome, GM, posição **r** e velocidade **v** |
| `sistema.h` | Tipo `Sistema`: vetor de corpos, quantidade de corpos e tempo atual |
| `forcas.h` | Funções que calculam a aceleração de cada corpo: Kepler, Newton N corpos, correção relativística |
| `integradores.h` | Funções que avançam o `Sistema` em um passo Δt: Euler semi-implícito, Velocity Verlet, RK4 |
| `io.h` | Ler o JSON de condições iniciais e a config; escrever trajetórias e energia em CSV |
| `apps/simular.c` | `main()`: lê a config, monta o sistema, roda o laço de integração e salva os resultados |
| `tests/` | Testes automáticos da física (ver seção 7) |

**Por que `include/orbital/`?** O subdiretório funciona como um "sobrenome" para os headers. No código, a inclusão fica `#include "orbital/corpo.h"`, e o nome não colide com headers de outras bibliotecas que também tenham um `io.h`, por exemplo.

**Por que `forcas` e `integradores` são separados?** Porque são escolhas independentes. Qualquer modelo de força pode ser combinado com qualquer integrador. É isso que permite os experimentos comparativos (por exemplo, "Newton + Verlet" contra "Newton + RK4").

**Por que existe `Sistema`?** No problema de N corpos, a aceleração da Terra depende da posição de todos os outros corpos ao mesmo tempo. Na versão antiga, cada planeta era atualizado sozinho, olhando apenas para o Sol, o que impede a interação entre planetas.

### 4.2 `analysis/`: o laboratório (Python)

| Arquivo | Responsabilidade |
|---|---|
| `orbital_data/horizons.py` | Monta a requisição, consulta o cache, chama a API e salva a resposta bruta com metadados |
| `orbital_data/corpos.py` | Tabela com nome, ID do Horizons e GM de cada corpo simulado |
| `orbital_data/conversao.py` | Extrai os números da resposta bruta e gera os arquivos de `data/processed/` e `data/reference/` |
| `scripts/baixar_condicoes_iniciais.py` | Baixa r e v de todos os corpos numa data (`--data 2000-01-01`) |
| `scripts/baixar_referencia.py` | Baixa a série temporal de gabarito (por exemplo, 2000 a 2100, passo de 10 dias) |
| `scripts/comparar_com_referencia.py` | Lê uma pasta de `results/`, compara com `data/reference/` e gera gráficos de erro |
| `notebooks/` | Explorações livres e figuras para os documentos |

**Pacote × scripts:** `orbital_data/` contém funções reutilizáveis, sem efeito ao ser importado. `scripts/` contém programas que se executam pela linha de comando e usam essas funções.

### 4.3 `data/`: a memória do projeto

| Pasta | Conteúdo | Regra | No Git? |
|---|---|---|---|
| `raw/horizons/<época>/` | Uma resposta da API por corpo, ex. `399.json` | **Imutável.** Nunca editar à mão. Se estiver errada, apagar e baixar de novo. | Sim |
| `processed/` | `ic_<época>.json`: condições iniciais de todos os corpos | Sempre gerada por `conversao.py` | Sim |
| `reference/` | `horizons_<início>-<fim>_passo<N>d.csv` | Gabarito para comparação | Sim, se pequeno |

> ⚠️ Nunca crie arquivos vazios de exemplo em `data/raw/`. O cache considera que um arquivo existente já foi baixado e deixa de buscá-lo.

### 4.4 `config/`

Cada arquivo descreve uma execução. Exemplo (`simulacao_padrao.json`):

```json
{
    "condicoes_iniciais": "data/processed/ic_2000-01-01.json",
    "modelo_forca": "newton",
    "integrador": "verlet",
    "passo_dias": 0.0416667,
    "duracao_dias": 36525,
    "salvar_a_cada_dias": 10,
    "saida": "results/"
}
```

`passo_dias` de 0,0416667 equivale a 1 hora, e 36 525 dias equivalem a 100 anos julianos.

### 4.5 `results/`

Cada execução cria uma pasta com nome `<data>_<modelo>_<integrador>_dt<passo>`, contendo:

| Arquivo | Conteúdo |
|---|---|
| `config_usada.json` | Cópia exata da config, para saber depois como o resultado foi gerado |
| `trajetorias.csv` | Colunas `t_dias, id, x, y, z, vx, vy, vz` |
| `energia.csv` | Colunas `t_dias, energia, erro_relativo` |

A pasta é ignorada pelo Git porque tudo nela pode ser regenerado. As figuras finais vão para `docs/`.

### 4.6 `web/` e `legacy/`

- `web/` vai receber a visualização em Three.js, usando o próprio motor em C compilado para WebAssembly.
- `legacy/` guarda a primeira versão do projeto. Cada parte será migrada e o diretório será removido ao final da Fase 1:

| Arquivo antigo | Destino na nova estrutura |
|---|---|
| `planetas.c` / `planetas.h` | `corpo.c`, `integradores.c` (o Euler semi-implícito é reaproveitado) |
| `main.c` | `apps/simular.c` + a leitura de JSON em `io.c` |
| `api_planeta.py` | Aposentado: a API Ninjas é substituída pelo JPL Horizons |

---

## 5. Regras de uso da API

**Regra 1: uma única porta de entrada.** Só `analysis/orbital_data/horizons.py` faz requisições HTTP. Se a API mudar, só um arquivo muda.

**Regra 2: cache antes de rede.** Antes de baixar, verificar se o arquivo já existe em `data/raw/`. Isso poupa o servidor do JPL e garante que você sempre trabalhe com o mesmo dado.

**Regra 3: guardar a resposta bruta com metadados.** Junto com a resposta, salvar a data da requisição, a URL e todos os parâmetros. Um número sem unidade e sem referencial não tem valor científico.

**Regra 4: o C nunca vê a API.** O motor lê apenas `data/processed/` e `config/`.

### 5.1 A API do JPL Horizons

- **Endpoint:** `https://ssd.jpl.nasa.gov/api/horizons.api`
- **Autenticação:** nenhuma
- **Documentação:** <https://ssd-api.jpl.nasa.gov/doc/horizons.html>

Parâmetros padrão do projeto:

| Parâmetro | Valor | Significado |
|---|---|---|
| `format` | `json` | Formato do envelope da resposta |
| `COMMAND` | `'399'` | ID do corpo (ver tabela abaixo) |
| `EPHEM_TYPE` | `'VECTORS'` | Vetores de estado (r, v) |
| `CENTER` | `'500@0'` | Origem no baricentro do Sistema Solar |
| `REF_PLANE` | `'ECLIPTIC'` | Plano da órbita da Terra em J2000 |
| `REF_SYSTEM` | `'ICRF'` | Referencial inercial internacional |
| `OUT_UNITS` | `'AU-D'` | Unidades: UA e UA/dia |
| `VEC_TABLE` | `'2'` | Somente posição e velocidade |
| `START_TIME` / `STOP_TIME` | `'2000-01-01'` / `'2000-01-02'` | Intervalo |
| `STEP_SIZE` | `'1 d'` | Passo da tabela |

A resposta traz um campo `result` com texto. Os números ficam entre os marcadores `$$SOE` (*start of ephemeris*) e `$$EOE` (*end of ephemeris*).

### 5.2 IDs dos corpos

| Corpo | ID do centro | ID do baricentro do sistema |
|---|---|---|
| Sol | 10 | — |
| Mercúrio | 199 | 1 |
| Vênus | 299 | 2 |
| Terra | 399 | 3 (Terra + Lua) |
| Lua | 301 | — |
| Marte | 499 | 4 |
| Júpiter | 599 | 5 |
| Saturno | 699 | 6 |
| Urano | 799 | 7 |
| Netuno | 899 | 8 |

**Qual usar?** Para simular só os planetas, é melhor usar os **baricentros dos sistemas** (1 a 8). O baricentro de Júpiter, por exemplo, já inclui a massa das luas, e é esse ponto que segue uma órbita suave ao redor do Sol. O centro do planeta oscila em torno dele.

---

## 6. Convenções científicas

| Decisão | Escolha | Por quê |
|---|---|---|
| Unidades | UA, dia, UA³/dia² | São as do Horizons, e os números ficam perto de 1 (menos erro de arredondamento que valores na casa de 10¹¹) |
| Massa | Guardar **GM**, nunca G e M separados | GM do Sol é conhecido com ~11 dígitos; G sozinho, com ~5 |
| Origem | Baricentro do Sistema Solar | O Sol também se move, puxado principalmente por Júpiter |
| Plano | Eclíptica J2000 | Padrão para dinâmica de planetas |
| Tempo | TDB (Tempo Dinâmico Baricêntrico) | Escala usada pelas efemérides; difere do UTC em ~69 s |
| Época inicial | 2000-01-01 | Próxima da época padrão J2000.0 |

---

## 7. Testes do motor

| Teste | O que verifica | Critério de aprovação |
|---|---|---|
| `test_vetor3.c` | Operações de vetor com valores conhecidos | Igualdade dentro de 10⁻¹² |
| `test_orbita_circular.c` | Um corpo em órbita circular volta ao ponto inicial após um período | Erro de posição pequeno e diminuindo com Δt |
| `test_conservacao_energia.c` | A energia total do sistema não deriva | Erro relativo limitado ao longo de muitas órbitas |

---

## 8. Convenções de código

- **C:** padrão C11, nomes em `snake_case`, tipos em `PascalCase` (`Corpo`, `Sistema`), headers com *include guards* `ORBITAL_<NOME>_H`.
- **Python:** PEP 8, funções com *docstrings*, caminhos montados a partir da raiz do projeto (nunca relativos ao diretório onde o comando foi executado).
- **Nomes de arquivo de dados:** sempre carregam a época e o passo, como `ic_2000-01-01.json` ou `horizons_2000-2100_passo10d.csv`.
