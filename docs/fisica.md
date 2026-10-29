# A física do Simulador Orbital

Este documento reúne todas as equações que o simulador usa. Cada tema segue a mesma ordem: **definição** científica, **desenvolvimento** do conceito e **exemplo** com números reais.

## Sumário

1. [Unidades e constantes](#1-unidades-e-constantes)
2. [Vetor de estado](#2-vetor-de-estado)
3. [Lei da Gravitação Universal](#3-lei-da-gravitação-universal)
4. [Problema de dois corpos e as leis de Kepler](#4-problema-de-dois-corpos-e-as-leis-de-kepler)
5. [Problema de N corpos](#5-problema-de-n-corpos)
6. [Integração numérica](#6-integração-numérica)
7. [Grandezas conservadas](#7-grandezas-conservadas)
8. [Correção da relatividade geral](#8-correção-da-relatividade-geral)
9. [Referenciais e escalas de tempo](#9-referenciais-e-escalas-de-tempo)
10. [Referências](#10-referências)

---

## 1. Unidades e constantes

### Definição

Um **sistema de unidades** é o conjunto de grandezas de referência em que todos os números do programa são expressos. O simulador usa o sistema astronômico:

| Grandeza | Unidade | Valor no SI |
|---|---|---|
| Distância | unidade astronômica (UA) | 1 UA = 149 597 870 700 m (exato, por definição da IAU) |
| Tempo | dia | 1 dia = 86 400 s |
| Parâmetro gravitacional | UA³/dia² | — |

### Desenvolvimento

**Por que não usar metros e segundos?** Em metros, a posição da Terra é da ordem de 10¹¹ e a de Netuno de 10¹². Em UA, esses valores ficam entre 0,4 e 30. Os números de ponto flutuante (`double`) têm cerca de 16 dígitos significativos em qualquer escala, mas as contas intermediárias (quadrados, cubos, divisões) ficam mais bem comportadas com valores perto de 1. Além disso, UA e dia são as unidades nativas do JPL Horizons, o que evita conversões.

**Por que GM e não G × M?** A constante gravitacional G é conhecida com apenas uns 5 algarismos significativos, porque é medida em laboratório com forças muito fracas. Já o produto GM de um corpo celeste é medido diretamente pelo movimento dos objetos ao seu redor, com precisão muito maior. Para o Sol:

$$GM_\odot = 1{,}32712440041 \times 10^{20}\ \text{m}^3/\text{s}^2 \quad (\sim 11\ \text{algarismos})$$

Multiplicar um G impreciso por uma massa (que também foi deduzida de GM) só joga precisão fora. Por isso o projeto guarda o **GM** de cada corpo, e a palavra "massa" aparece no código sempre como GM.

### Exemplo

A **constante gravitacional de Gauss** é k = 0,01720209895, definida historicamente de forma que, em UA e dias:

$$GM_\odot = k^2 = 2{,}9591220828559 \times 10^{-4}\ \text{UA}^3/\text{dia}^2$$

A velocidade da luz, necessária na seção 8, vale c = 299 792,458 km/s = **173,1446 UA/dia**.

---

## 2. Vetor de estado

### Definição

O **vetor de estado** de um corpo é o par posição–velocidade num instante t:

$$\vec{r} = (x,\ y,\ z), \qquad \vec{v} = (v_x,\ v_y,\ v_z)$$

Para equações diferenciais de segunda ordem, como as de Newton, esse par determina completamente todo o movimento futuro e passado.

### Desenvolvimento

O estado do sistema inteiro é a lista dos vetores de estado de todos os corpos, mais o tempo atual. É exatamente o que o tipo `Sistema` guarda em C. Simular significa transformar o estado em t no estado em t + Δt, repetidas vezes.

A versão antiga do projeto trabalhava em 2D e inventava o estado inicial (planeta no eixo x, velocidade circular no eixo y). Agora o estado inicial vem do JPL Horizons, em 3D, numa data real.

### Exemplo

Em 2000-01-01, a Terra está a cerca de 0,98 UA do Sol (perto do periélio, que ocorre no início de janeiro) e se move a cerca de 0,0175 UA/dia, ou ~30,3 km/s. Os valores exatos virão do arquivo `data/processed/ic_2000-01-01.json`.

---

## 3. Lei da Gravitação Universal

### Definição

Dois corpos de massas M e m, separados por uma distância r, se atraem com uma força de intensidade

$$F = \frac{G\,M\,m}{r^2}$$

dirigida ao longo da linha que os une.

### Desenvolvimento

Pela segunda lei de Newton (F = m·a), a massa m do corpo atraído se cancela. A aceleração depende só do GM de quem atrai e da posição relativa. Na forma vetorial, com **r** apontando do corpo que atrai até o corpo atraído:

$$\vec{a} = -\frac{GM}{|\vec{r}|^3}\,\vec{r}$$

O sinal negativo faz a aceleração apontar para quem atrai. O expoente 3 no denominador aparece porque |**r**|² vem da lei e o terceiro |**r**| normaliza o vetor **r** em uma direção de tamanho 1.

**Dica numérica:** calcule r² = x² + y² + z² uma vez, depois r³ = r² · √r². Evite `pow(r, 3)`, que é mais lento e não traz ganho de precisão.

### Exemplo

A aceleração que o Sol provoca na Terra (r = 1 UA):

$$a = \frac{2{,}959 \times 10^{-4}}{1^2} = 2{,}959 \times 10^{-4}\ \text{UA/dia}^2 \approx 5{,}93 \times 10^{-3}\ \text{m/s}^2$$

Cerca de 1 650 vezes menor que a gravidade na superfície da Terra, mas suficiente para curvar a trajetória da Terra num círculo de 150 milhões de km.

---

## 4. Problema de dois corpos e as leis de Kepler

### Definição

O **problema de dois corpos** é o movimento de dois corpos que interagem apenas pela gravidade entre si. Ele tem solução exata: a órbita relativa é uma **cônica** (elipse, parábola ou hipérbole), descrita pelas três leis de Kepler.

1. As órbitas são elipses com o Sol num dos focos.
2. A linha Sol–planeta varre áreas iguais em tempos iguais.
3. O quadrado do período é proporcional ao cubo do semieixo maior: T² = 4π² a³ / GM.

### Desenvolvimento

**Elementos orbitais.** Uma elipse no espaço é descrita por seis números, equivalentes aos seis números do vetor de estado:

| Elemento | Símbolo | O que descreve |
|---|---|---|
| Semieixo maior | a | Tamanho da órbita |
| Excentricidade | e | Achatamento (0 = círculo) |
| Inclinação | i | Inclinação do plano da órbita em relação à eclíptica |
| Longitude do nodo ascendente | Ω | Onde a órbita cruza a eclíptica subindo |
| Argumento do periélio | ω | Orientação da elipse dentro do seu plano |
| Anomalia média | M | Posição do corpo na órbita num instante |

**A equação de Kepler.** A anomalia média cresce uniformemente no tempo, M = n (t − t₀), com o movimento médio n = √(GM/a³). Para achar onde o corpo está, resolve-se a **equação de Kepler** para a anomalia excêntrica E:

$$M = E - e\,\sin E$$

Ela não tem solução algébrica. Resolve-se pelo **método de Newton-Raphson**, partindo de E₀ = M:

$$E_{k+1} = E_k - \frac{E_k - e\sin E_k - M}{1 - e\cos E_k}$$

Depois, a anomalia verdadeira ν (o ângulo real a partir do periélio) e a distância r:

$$\tan\frac{\nu}{2} = \sqrt{\frac{1+e}{1-e}}\,\tan\frac{E}{2}, \qquad r = a\,(1 - e\cos E)$$

Por fim, três rotações (por ω, i e Ω) levam a posição do plano da órbita para o referencial da eclíptica.

**Equação vis-viva.** A velocidade em qualquer ponto da órbita é

$$v^2 = GM\left(\frac{2}{r} - \frac{1}{a}\right)$$

Ela serve para conferir resultados: se o simulador der uma velocidade diferente da prevista pela vis-viva numa órbita de dois corpos, há um erro.

**Limitação.** No Sistema Solar real há mais de dois corpos. Júpiter, Saturno e os outros planetas perturbam cada órbita, e os elementos orbitais mudam lentamente com o tempo. Esse é o **nível 1** do simulador: ele erra justamente por ignorar essas perturbações, e medir esse erro é o primeiro experimento.

### Exemplo

**Terceira lei para a Terra.** Com a = 1 UA:

$$T = 2\pi\sqrt{\frac{a^3}{GM_\odot}} = \frac{2\pi}{k} = 365{,}2569\ \text{dias}$$

É o **ano sideral**, o tempo para a Terra voltar à mesma posição em relação às estrelas.

**Vis-viva para a Terra** (a = 1,000003 UA, e = 0,0167):

| Ponto | Distância | Velocidade |
|---|---|---|
| Periélio (início de janeiro) | 0,9833 UA | 30,29 km/s |
| Afélio (início de julho) | 1,0167 UA | 29,29 km/s |

**Equação de Kepler para Mercúrio** (e = 0,2056) com M = 1 rad:

| Iteração | E (rad) |
|---|---|
| 0 | 1,000000 |
| 1 | 1,194627 |
| 2 | 1,190946 |
| 3 | 1,190945 |

Convergência em 3 iterações. Resultado: ν = 79,7° e r = 0,3576 UA.

---

## 5. Problema de N corpos

### Definição

O **problema de N corpos** é o movimento de N corpos que se atraem gravitacionalmente aos pares. A aceleração do corpo i é a soma das atrações de todos os outros:

$$\vec{a}_i = -\sum_{j \ne i} \frac{GM_j}{|\vec{r}_i - \vec{r}_j|^3}\,(\vec{r}_i - \vec{r}_j)$$

### Desenvolvimento

Para N ≥ 3, não há solução analítica geral (Poincaré, 1890). A única saída é a **integração numérica** (seção 6).

**Custo.** Cada corpo sente todos os outros, então são N(N−1)/2 pares por passo. Para 9 corpos, são 36 pares, um custo irrelevante. Para milhares de asteroides, entra uma simplificação: eles são **partículas de teste**, que sentem os planetas mas não os atraem (massa desprezível). O custo passa a crescer só linearmente com o número de asteroides.

**Terceira lei de Newton no código.** A força de j sobre i é igual e oposta à de i sobre j. Calculando cada par uma vez e aplicando aos dois corpos, o custo cai pela metade.

**Baricentro.** O centro de massa do sistema não acelera, porque não há forças externas. Por isso ele é a origem natural do referencial. O Sol **não** fica parado: ele se move ao redor do baricentro, puxado principalmente por Júpiter.

$$\vec{R}_{cm} = \frac{\sum_i GM_i\,\vec{r}_i}{\sum_i GM_i}$$

Esse é o **nível 2** do simulador.

### Exemplo

**Quanto o Sol se move por causa de Júpiter?** Considerando só os dois corpos, a distância do Sol ao baricentro é

$$d = a_J\,\frac{M_J}{M_\odot + M_J} = 5{,}2\ \text{UA} \times \frac{1}{1048} \approx 742\ 000\ \text{km}$$

Cerca de **1,07 raio solar**: o baricentro Sol–Júpiter fica logo fora da superfície do Sol. É por isso que a versão antiga, com o Sol fixo na origem, já começava errada.

---

## 6. Integração numérica

### Definição

**Integrar numericamente** uma equação diferencial é aproximar sua solução em passos discretos de tempo Δt. A **ordem** p de um método indica como o erro acumulado diminui com o passo: erro ∝ Δtᵖ. Dividir Δt por 2 reduz o erro por 2ᵖ.

Um integrador é **simplético** quando preserva a estrutura geométrica das equações de Hamilton. Na prática, a energia não deriva: ela oscila em torno do valor correto por tempos muito longos.

### Desenvolvimento

Os quatro métodos do projeto, para um passo de **r**ₙ, **v**ₙ a **r**ₙ₊₁, **v**ₙ₊₁, com **a**(**r**) dada pela seção 3 ou 5:

**Euler explícito** (ordem 1, não simplético). Só para mostrar o que não fazer:

$$\vec{r}_{n+1} = \vec{r}_n + \vec{v}_n\,\Delta t, \qquad \vec{v}_{n+1} = \vec{v}_n + \vec{a}(\vec{r}_n)\,\Delta t$$

O planeta ganha energia a cada volta e espirala para fora.

**Euler semi-implícito** (ordem 1, simplético). O método da versão antiga do projeto. Atualiza primeiro a velocidade e usa a velocidade nova na posição:

$$\vec{v}_{n+1} = \vec{v}_n + \vec{a}(\vec{r}_n)\,\Delta t, \qquad \vec{r}_{n+1} = \vec{r}_n + \vec{v}_{n+1}\,\Delta t$$

**Velocity Verlet** (ordem 2, simplético, reversível no tempo). O método principal do projeto:

$$\vec{v}_{n+1/2} = \vec{v}_n + \tfrac{1}{2}\,\vec{a}(\vec{r}_n)\,\Delta t$$

$$\vec{r}_{n+1} = \vec{r}_n + \vec{v}_{n+1/2}\,\Delta t$$

$$\vec{v}_{n+1} = \vec{v}_{n+1/2} + \tfrac{1}{2}\,\vec{a}(\vec{r}_{n+1})\,\Delta t$$

Ele custa uma avaliação de aceleração por passo, igual ao Euler, porque **a**(**r**ₙ₊₁) é reaproveitada no passo seguinte.

**Runge-Kutta de 4ª ordem, RK4** (ordem 4, não simplético). Avalia a derivada quatro vezes por passo e combina os resultados. Para o estado **y** = (**r**, **v**) com **y**' = **f**(**y**) = (**v**, **a**(**r**)):

$$\vec{k}_1 = \vec{f}(\vec{y}_n), \quad \vec{k}_2 = \vec{f}\!\left(\vec{y}_n + \tfrac{\Delta t}{2}\vec{k}_1\right), \quad \vec{k}_3 = \vec{f}\!\left(\vec{y}_n + \tfrac{\Delta t}{2}\vec{k}_2\right), \quad \vec{k}_4 = \vec{f}(\vec{y}_n + \Delta t\,\vec{k}_3)$$

$$\vec{y}_{n+1} = \vec{y}_n + \frac{\Delta t}{6}\left(\vec{k}_1 + 2\vec{k}_2 + 2\vec{k}_3 + \vec{k}_4\right)$$

Muito preciso em intervalos curtos, mas a energia deriva lentamente sempre no mesmo sentido. Em séculos de simulação, um Verlet com passo menor pode vencer um RK4.

| Método | Ordem | Simplético | Acelerações por passo | Comportamento da energia |
|---|---|---|---|---|
| Euler explícito | 1 | Não | 1 | Cresce sem parar |
| Euler semi-implícito | 1 | Sim | 1 | Oscila, sem deriva |
| Velocity Verlet | 2 | Sim | 1 | Oscila, sem deriva |
| RK4 | 4 | Não | 4 | Erro pequeno, mas com deriva |

**Escolha do passo Δt.** O passo precisa ser bem menor que o menor período do sistema. Uma regra prática é ter pelo menos algumas centenas de passos por órbita do corpo mais rápido (Mercúrio, com período de 88 dias).

### Exemplo

Com Δt = 1 hora, Mercúrio completa uma órbita em 88 × 24 ≈ **2 111 passos**. Simular 100 anos com 9 corpos dá cerca de 877 000 passos × 36 pares ≈ 32 milhões de cálculos de atração, o que leva poucos segundos em C.

O experimento E2 (ver [validacao.md](validacao.md)) mede na prática a ordem de cada método: ao dividir Δt por 2, o erro do Verlet deve cair ~4 vezes e o do RK4 ~16 vezes.

---

## 7. Grandezas conservadas

### Definição

Uma **grandeza conservada** é uma combinação do estado do sistema que não muda com o tempo. Para N corpos isolados, conservam-se a energia total, o momento linear total e o momento angular total.

### Desenvolvimento

Como o projeto guarda GM e não M, as fórmulas usam GM no lugar da massa. O resultado fica multiplicado pela constante G, o que não muda a conservação:

$$\tilde{E} = \sum_i \tfrac{1}{2}\,GM_i\,|\vec{v}_i|^2 \;-\; \sum_{i<j} \frac{GM_i\,GM_j}{|\vec{r}_i - \vec{r}_j|} \qquad (\tilde{E} = G \cdot E)$$

$$\tilde{\vec{L}} = \sum_i GM_i\,(\vec{r}_i \times \vec{v}_i) \qquad (\tilde{\vec{L}} = G \cdot \vec{L})$$

Na solução exata essas grandezas são constantes. Na simulação, elas variam um pouco por causa dos erros numéricos. O **erro relativo de energia**

$$\delta E(t) = \left|\frac{\tilde{E}(t) - \tilde{E}(0)}{\tilde{E}(0)}\right|$$

é o termômetro da qualidade da integração, e ele pode ser calculado sem nenhum dado externo.

### Exemplo

Para a Terra sozinha ao redor do Sol, a energia específica (por unidade de massa) é

$$\varepsilon = -\frac{GM_\odot}{2a} = -1{,}48 \times 10^{-4}\ \text{UA}^2/\text{dia}^2$$

Ela é negativa porque a órbita é ligada (fechada). Uma simulação com Euler explícito mostraria ε subindo a cada volta em direção a zero, que é o limite de escape.

---

## 8. Correção da relatividade geral

### Definição

A **relatividade geral** descreve a gravidade como curvatura do espaço-tempo. Para campos fracos e velocidades baixas, como no Sistema Solar, ela pode ser escrita como a gravidade de Newton mais pequenas correções em potências de (v/c)². A primeira correção é o termo **pós-newtoniano de primeira ordem (1PN)**.

### Desenvolvimento

Para um corpo orbitando o Sol, considerando só a correção devida ao Sol (a dominante), a aceleração extra é

$$\vec{a}_{\text{RG}} = \frac{GM_\odot}{c^2\,r^3}\left[\left(\frac{4\,GM_\odot}{r} - v^2\right)\vec{r} + 4\,(\vec{r}\cdot\vec{v})\,\vec{v}\right]$$

com **r** e **v** relativos ao Sol. Ela é cerca de 10⁸ vezes menor que a newtoniana, mas tem um efeito que se acumula: faz o periélio avançar a cada órbita de

$$\Delta\varpi = \frac{6\pi\,GM_\odot}{c^2\,a\,(1 - e^2)}\ \text{radianos por órbita}$$

O efeito é maior para o planeta mais próximo do Sol (a pequeno) e com órbita mais excêntrica (e grande): Mercúrio.

Esse é o **nível 3** do simulador.

### Exemplo

Para Mercúrio, a = 0,3871 UA e e = 0,2056:

$$\Delta\varpi = 5{,}02 \times 10^{-7}\ \text{rad/órbita}$$

Em um século, Mercúrio dá 36 525 / 87,97 ≈ 415,2 voltas:

$$415{,}2 \times 5{,}02 \times 10^{-7}\ \text{rad} \approx 2{,}08 \times 10^{-4}\ \text{rad} \approx \mathbf{43{,}0''\ \text{por século}}$$

| Causa da precessão do periélio de Mercúrio | Valor aproximado |
|---|---|
| Perturbações dos outros planetas (Newton) | ~531″/século |
| Relatividade geral | ~43″/século |
| **Total observado** (num referencial inercial) | **~574″/século** |

No século XIX, Le Verrier percebeu que sobravam ~43″ sem explicação. Einstein calculou exatamente esse valor em 1915, numa das primeiras confirmações da relatividade geral. O experimento E4 reproduz essa história.

---

## 9. Referenciais e escalas de tempo

### Definição

Um **referencial** é o sistema de eixos e a origem em relação aos quais as posições são medidas. Uma **escala de tempo** é a definição de como se conta o tempo. Comparar dois resultados só faz sentido se ambos usarem o mesmo referencial e a mesma escala.

### Desenvolvimento

| Escolha | Valor no projeto | Significado |
|---|---|---|
| Sistema de referência | ICRF | Eixos fixos em relação a quasares distantes: um referencial inercial |
| Plano fundamental | Eclíptica J2000 | O plano z = 0 é o plano médio da órbita da Terra em 01/01/2000 |
| Origem | Baricentro do Sistema Solar | O ponto que não acelera (seção 5) |
| Escala de tempo | TDB | Tempo coordenado usado nas equações de movimento das efemérides |

**Por que TDB e não o horário do relógio?** O UTC tem segundos intercalares e acompanha a rotação irregular da Terra. As equações de movimento exigem um tempo uniforme. Em 2026, TDB − UTC ≈ 69 s. Parece pouco, mas a Terra anda 69 × 30 ≈ 2 000 km nesse intervalo.

### Exemplo

Se as condições iniciais forem pedidas no plano do equador da Terra (`REF_PLANE = 'FRAME'`) e o gabarito no plano da eclíptica, as coordenadas z diferem por uma rotação de 23,44° (a obliquidade da eclíptica). A comparação daria erros enormes que não têm nada a ver com a física simulada. Por isso todos os pedidos ao Horizons usam os mesmos parâmetros (ver [arquitetura.md](arquitetura.md#51-a-api-do-jpl-horizons)).

---

## 10. Referências

- Murray, C. D. & Dermott, S. F. *Solar System Dynamics*. Cambridge University Press, 1999. Referência clássica de dinâmica orbital.
- Curtis, H. D. *Orbital Mechanics for Engineering Students*. Elsevier. Excelente para Kepler e, no futuro, para foguetes.
- Hairer, E., Lubich, C. & Wanner, G. *Geometric Numerical Integration*. Springer. A teoria dos integradores simpléticos.
- Park, R. S. et al. "The JPL Planetary and Lunar Ephemerides DE440 and DE441". *The Astronomical Journal* 161:105, 2021.
- JPL Solar System Dynamics, elementos orbitais aproximados dos planetas: <https://ssd.jpl.nasa.gov/planets/approx_pos.html>
- JPL Horizons: <https://ssd.jpl.nasa.gov/horizons/>
