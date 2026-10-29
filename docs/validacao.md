# Validação do Simulador Orbital

Este documento é o caderno de laboratório do projeto: como saber se o simulador está certo, quais experimentos serão feitos e o que cada um mostrou.

---

## 1. Conceito

### Definição

**Validar** um modelo é verificar, com evidência quantitativa, se ele representa a realidade com a precisão necessária. Em simulação científica, costuma-se separar duas perguntas:

- **Verificação:** o código resolve corretamente as equações escolhidas? (Isso é um problema de programação e de matemática.)
- **Validação:** as equações escolhidas representam bem o mundo real? (Isso é um problema de física.)

### Desenvolvimento

As duas perguntas exigem referências diferentes:

| Pergunta | Referência usada | Exemplo de teste |
|---|---|---|
| Verificação | Soluções exatas e leis de conservação | Uma órbita circular de dois corpos deve se fechar; a energia não pode derivar |
| Validação | Efemérides do JPL Horizons (DE440) | A posição simulada de Marte em 2050 deve bater com a do Horizons |

Um erro grande na validação só pode ser atribuído à física depois que a verificação passou. Se não, não dá para saber se a culpa é do modelo ou de um bug.

### Exemplo

Se o nível 2 (Newton) errar a posição de Mercúrio em alguns milhares de km depois de um século, há duas explicações possíveis: um defeito no integrador ou a falta da relatividade geral. O experimento E2 (convergência) elimina a primeira hipótese: se diminuir Δt não reduz o erro, ele não é numérico. Só então o experimento E4 pode atribuir a diferença à relatividade.

---

## 2. Métricas

| Métrica | Fórmula | Unidade | O que mede |
|---|---|---|---|
| Erro de posição | Δr(t) = \|**r**(simulado) − **r**(Horizons)\| | km | Distância entre a posição simulada e a do Horizons |
| Erro relativo de energia | δE(t) = \|(Ẽ(t) − Ẽ(0)) / Ẽ(0)\| | adimensional | Qualidade numérica da integração (ver [fisica.md §7](fisica.md#7-grandezas-conservadas)) |
| Erro de momento angular | \|**L̃**(t) − **L̃**(0)\| / \|**L̃**(0)\| | adimensional | Idem, para a rotação do sistema |
| Precessão do periélio | taxa de variação de ϖ | ″/século | Efeito acumulado das perturbações e da relatividade |
| Ordem medida | p = log₂(erro(Δt) / erro(Δt/2)) | adimensional | Se o integrador tem a ordem teórica |

**Convenção para comparar com o Horizons:** as condições iniciais e o gabarito devem ser baixados com os mesmos parâmetros (referencial, plano, origem, unidades e escala de tempo). Ver [arquitetura.md §5.1](arquitetura.md#51-a-api-do-jpl-horizons).

---

## 3. Experimentos planejados

Cada experimento tem uma hipótese escrita **antes** de rodar. Assim, um resultado inesperado fica evidente, em vez de ser racionalizado depois.

### E1: Kepler contra a realidade (nível 1)

- **Pergunta:** quanto erra um modelo que ignora a atração entre os planetas?
- **Método:** propagar cada planeta pelo modelo de dois corpos a partir de 2000-01-01 e comparar com o Horizons por 100 anos.
- **Hipótese:** o erro cresce com o tempo. Ele deve ser maior para Saturno, Urano e Netuno, que se perturbam fortemente entre si e com Júpiter, e para o próprio Júpiter, perturbado por Saturno.
- **Saída:** gráfico Δr × tempo, uma curva por planeta, eixo vertical logarítmico.

### E2: convergência dos integradores (verificação)

- **Pergunta:** os integradores têm a ordem teórica?
- **Método:** simular 10 anos com Newton N corpos usando Δt = 4 h, 2 h, 1 h e 30 min. Como referência, usar a execução com o menor passo ou o REBOUND.
- **Hipótese:** ao dividir Δt por 2, o erro cai ~2× (Euler semi-implícito), ~4× (Verlet) e ~16× (RK4).
- **Saída:** gráfico log-log de erro × Δt. A inclinação de cada reta é a ordem p.

### E3: estabilidade de longo prazo (verificação)

- **Pergunta:** a energia se conserva por muito tempo?
- **Método:** simular 10 000 anos com Euler explícito, Euler semi-implícito, Verlet e RK4, com o mesmo Δt.
- **Hipótese:** Euler explícito diverge; os simpléticos oscilam sem deriva; o RK4 deriva lentamente.
- **Saída:** gráfico δE × tempo, eixo vertical logarítmico.

### E4: a precessão de Mercúrio (níveis 2 e 3)

- **Pergunta:** o simulador reproduz o efeito da relatividade geral?
- **Método:** simular 1 000 anos com Newton e com Newton + correção 1PN. Medir a longitude do periélio de Mercúrio ao longo do tempo e ajustar uma reta.
- **Hipótese:** Newton dá ~531″/século e Newton + relatividade dá ~574″/século. A diferença deve ser ~43″/século.
- **Cuidado:** o valor de 574″ vale num referencial inercial. Valores maiores (~5 600″) que aparecem na literatura incluem a precessão dos equinócios da Terra, que é um efeito do referencial, não da órbita de Mercúrio.
- **Saída:** gráfico de ϖ × tempo para os dois modelos e uma tabela com as taxas medidas.

### E5: Newton contra a realidade (nível 2)

- **Pergunta:** com N corpos, quanto o erro diminui em relação a Kepler?
- **Método:** igual ao E1, com o modelo de N corpos.
- **Hipótese:** o erro cai várias ordens de grandeza. O que sobra vem da relatividade, das luas, dos asteroides e das diferenças de modelo em relação à DE440.
- **Saída:** o mesmo gráfico do E1, para comparar lado a lado.

### E6: Apophis em 2029 (fase dos asteroides)

- **Pergunta:** o simulador prevê corretamente uma aproximação próxima à Terra?
- **Método:** integrar o asteroide 99942 Apophis como partícula de teste a partir de condições iniciais de 2026 até abril de 2029.
- **Hipótese:** maior aproximação em 13/04/2029, a cerca de 38 000 km do centro da Terra (~32 000 km da superfície).
- **Saída:** distância Terra–Apophis × tempo, com a data e a distância mínima comparadas às do JPL.

---

## 4. Testes automáticos

Ficam em `core/tests/` e rodam com `make test`. Eles garantem que mudanças no código não quebrem a física já validada.

| Teste | Situação | Critério de aprovação |
|---|---|---|
| `test_vetor3.c` | Operações com valores conhecidos, ex. \|(3, 4, 0)\| = 5 | Diferença < 10⁻¹² |
| `test_orbita_circular.c` | Um corpo a 1 UA com velocidade circular √(GM/r) por um período T = 2π/k | Volta ao ponto inicial com erro que diminui conforme a ordem do integrador |
| `test_conservacao_energia.c` | Sol + Terra + Júpiter por 1 000 anos com Verlet | δE permanece limitado (sem tendência de crescimento) |

---

## 5. Registro de resultados

Cada experimento concluído recebe uma linha aqui, com a pasta de `results/` que o gerou e o link do gráfico em `docs/figuras/`.

| Exp. | Data | Modelo / integrador / Δt | Resultado principal | Hipótese confirmada? | Figura |
|---|---|---|---|---|---|
| E1 | — | — | *pendente* | — | — |
| E2 | — | — | *pendente* | — | — |
| E3 | — | — | *pendente* | — | — |
| E4 | — | — | *pendente* | — | — |
| E5 | — | — | *pendente* | — | — |
| E6 | — | — | *pendente* | — | — |

### Modelo para registrar um experimento

```markdown
### E<N> — <título> (AAAA-MM-DD)

- Pasta de resultados: results/<nome-da-execução>/
- Configuração: modelo, integrador, Δt, duração, época inicial
- Resultado: <números principais, com unidades>
- Comparação com a hipótese: <confirmada / refutada / parcial, e por quê>
- Limitações: <o que pode ter afetado o resultado>
- Figura: ![descrição](figuras/e<N>_<nome>.png)
```

---

## 6. Referências de comparação

- **JPL Horizons (DE440):** gabarito principal de posições. <https://ssd.jpl.nasa.gov/horizons/>
- **REBOUND:** integrador N corpos de pesquisa (IAS15, WHFast), usado como segunda referência para separar erros numéricos de erros de modelo. <https://rebound.readthedocs.io/>
- **Precessão de Mercúrio:** Clemence, G. M. "The Relativity Effect in Planetary Motions". *Reviews of Modern Physics* 19, 361 (1947).
- **Apophis:** JPL Small-Body Database. <https://ssd.jpl.nasa.gov/tools/sbdb_lookup.html>
