# Detyra 4 – Torso Decompositions me metaheuristika

**Metaheuristics: Local Search**

## 1. Përshkrimi i problemit

Problemi vjen nga sfida e ESA **SpOC-3, Challenge 1: Torso Decompositions** ([optimise.esa.int](https://optimise.esa.int/challenge/spoc-3-torso-decompositions/About), [github.com/esa/SpOC3](https://github.com/esa/SpOC3)).

Jepet një **graf i padrejtuar** `G` me nyjet `0 … n−1`. Zgjidhja është një vektor:

```
x = [p₁, p₂, …, pₙ, t]
```

- `p` është një **permutacion** i nyjeve;
- `t` është **pragu**: **torso** janë `n − t` nyjet e fundit të permutacionit.

**Vlerësimi:**

1. Permutacioni i orienton brinjët: brinja `{u, v}` bëhet `(u → v)` nëse `u` është para `v`.
2. **Fill-in:** permutacioni lexohet nga e majta në të djathtë. Kur një nyje `u` ka dy brinjë dalëse drejt `v` dhe `w` që nuk janë të lidhura, shtohet brinja `{v, w}`.
3. `outdeg(u)` është numri i brinjëve dalëse të `u` në grafin e mbushur.
4. Dy objektivat janë:
   - **Torso size** `= n − t`, që **maksimizohet**;
   - **Torso width** `= max outdeg(u)` për `u` në torso, që **minimizohet**.

Problemi ka **dy objektiva në konflikt**: torso më e madhe zakonisht ka gjerësi më të madhe. Prandaj rezultati nuk është një zgjidhje e vetme, por një **front Pareto** prej deri në 20 vektorësh, i vlerësuar me **hypervolume**.

**Instancat zyrtare** janë te dosja [data/](data/), të shkarkuara nga ESA:

| Instanca | Problemi | Nyje | Brinjë | Dendësia mesatare |
|---|---|---|---|---|
| `easy.gr` | small-graph | 1,357 | 2,280 | 3.4 fqinjë |
| `medium.gr` | medium-graph | 1,399 | 13,799 | 19.7 fqinjë |
| `hard.gr` | large-graph | 2,426 | 253,895 | 209 fqinjë |

**Shembulli i detyrës:** grafi me 10 nyje dhe `x = [0,1,2,4,5,3,6,8,9,7, 6]` jep torso size = 4 dhe width = 2. Programi e jep të njëjtin rezultat (`python main.py --example`).

## 2. Modelimi

| Elementi | Në këtë problem |
|---|---|
| **Gjendja (zgjidhja)** | Një permutacion `p` i nyjeve; pragu `t` zgjidhet më vonë |
| **Hapësira e kërkimit** | `n!` permutacione, p.sh. `1357! ≈ 10^3663` për easy |
| **Objektivat** | maksimizo `n − t`, minimizo `width(t)` |
| **Fqinjësia** | **insertion move**: një nyje zhvendoset në një pozitë tjetër |
| **Kufizimi** | gjerësia mbi 500 numërohet si 501, pra nuk ka vlerë |

**Vëzhgimi kryesor:** një permutacion jep njëherësh zgjidhje për **të gjitha** pragjet `t`. Nëse `deg[i]` është shkalla dalëse e pozitës `i`, atëherë:

```
width(t) = max(deg[t], deg[t+1], …, deg[n−1])        (maksimumi i prapashtesës)
```

Nyjet në fund kanë shkallë të vogël, sepse kanë pak nyje pas tyre. Prandaj torsot e vogla kanë gjerësi të vogël, dhe vështirësia është të gjenden **torso të mëdha me gjerësi të vogël**.

## 3. Vlerësimi efikas

Shtimi i të gjitha brinjëve `{v, w}` do të kushtonte `O(deg²)` për çdo nyje. Përdoret një lehtësim i njohur (Tarjan & Yannakakis): kur procesohet nyja `u` me fqinjët e mëvonshëm `S`, mjafton që `S − {j}` t'i shtohet **vetëm** nyjes `j`, që është pozita më e hershme në `S`. Kur të procesohet `j`, ato bëhen fqinjët e tij dhe fill-in-i përhapet më tej. Rezultati është i njëjti graf i mbushur.

Bashkësitë ruhen si **bitmask** mbi pozitat (`int` i Python-it), prandaj bashkimi është një veprim `|`, dhe pozita më e hershme gjendet me `S & −S`.

| Instanca | Koha e një vlerësimi |
|---|---|
| easy | ~2 ms |
| medium | ~5 ms |
| hard | ~70 ms |

Implementimi gjendet te `out_degrees()` në [torso.py](torso.py).

## 4. Hypervolume

Për pikat `(t, width)`, ku të dyja minimizohen, dhe pikën e referencës `(n, 501)`:

```
HV = sipërfaqja e zonës që dominohet nga fronti dhe kufizohet nga pika e referencës
```

Për një permutacion me të gjitha pragjet: `HV = Σ_t (501 − width(t))`. Vlerat në tabela janë **të normalizuara** me `n · 501`, prandaj janë mes 0 dhe 1.

Përshkrimi i ESA nuk e jep pikën e referencës. Zgjedhja `(n, 501)` del nga rregulli "gjerësia mbi 500 numërohet si 501". Prej të gjitha pikave jo të dominuara, 20 zgjidhen me algoritëm greedy: në çdo hap shtohet pika që e rrit HV më së shumti (`Archive.select`).

## 5. Metaheuristikat

### Ideja: metoda epsilon-constraint

Optimizimi direkt i HV nuk funksionon mirë: një lëvizje e vetme rrallë ndryshon maksimumin e prapashtesës, prandaj kërkimi s'ka "drejtim". Prandaj problemi me dy objektiva ndahet në disa probleme me **një objektiv**, një për çdo gjerësi maksimale `k`:

```
maksimizo  size_k(p) = n − (pozita e fundit me deg > k) − 1
```

Të gjitha nyjet pas nyjes së fundit "shkelëse" (me `deg > k`) formojnë torso me gjerësi ≤ k.

**Funksioni objektiv i kërkimit:**

```
f_k(p) = size_k(p) − 0.01 · Σ_{i: deg[i] > k} (deg[i] − k)
```

Termi i dytë, **teprica e gjerësisë**, e udhëzon kërkimin edhe kur `size_k` nuk ndryshon: sa më pak tepricë, aq më afër jemi një torsoje më të madhe.

**Lëvizja (insertion move):** zgjidhet një nyje shkelëse dhe zhvendoset:
- 70% e rasteve merret një nga 5 të fundit, që janë ato që e kufizojnë torson; 30% merret cilado;
- 50% e rasteve zhvendoset më herët, 50% në një pozitë të rastësishme.

**Rrjedha e plotë** (`optimize`):

```
p₀ ← renditja minimum degree                          (heuristikë konstruktive)
w₀ ← gjerësia e plotë e p₀
për k në {w₀−1, …, 1} (shkallë gjeometrike, 12 vlera):
    fillimi ← permutacioni më i mirë i arkivit për gjerësi ≤ k     (warm start)
    METAHEURISTIKA(k, fillimi)             (SA ose ILS, koha e ndarë në mënyrë të barabartë)
    çdo permutacion i pranuar → ARKIVI PARETO     (jep pika për të gjitha k njëherësh)
kthe 20 pikat e arkivit me HV maksimal
```

### Heuristika fillestare: minimum degree

Heuristika klasike për elimination orderings: në çdo hap eliminohet nyja me shkallën më të vogël në grafin e mbetur, dhe fqinjët e saj lidhen mes vete. Kjo jep gjerësi të vogël për **të gjithë grafin**: 20 te easy, 285 te medium dhe 499 te hard. Megjithatë, nyjet më të dendura mbeten në fund. Prandaj torsot e mesme janë të këqija: me gjerësi `k` arrihet vetëm torso me `k + 1` nyje.

### Metaheuristika 1: Simulated Annealing (SA)

```
T ← 5
përderisa ka kohë:
    q ← fqinji i p (insertion move)
    Δ ← f_k(q) − f_k(p)
    nëse Δ ≥ 0 ose random() < e^(Δ / T) → p ← q          (kriteri i Metropolis)
    T ← ulet në mënyrë gjeometrike nga 5 në 0.05
```

Në fillim pranohen edhe lëvizje më të këqija, që të dilet nga minimumet lokale. Në fund kërkimi bëhet pothuajse hill climbing.

### Metaheuristika 2: Iterated Local Search (ILS)

```
përderisa ka kohë:
    q ← fqinji i p;  nëse f_k(q) ≥ f_k(p) → p ← q        (hill climbing)
    nëse 60 hapa pa përmirësim:
        p ← më e mira + 8 lëvizje të rastësishme        (perturbation)
```

ILS pranon vetëm lëvizje që nuk e përkeqësojnë zgjidhjen. Kur ngec në minimum lokal, e "shkund" zgjidhjen më të mirë dhe vazhdon prej saj.

## 6. Rezultatet

Rezultatet merren me `python main.py <instanca> -m <metoda> --time <s> --out results/...`, me seed 0. Koha e kërkimit është 300 s për easy dhe medium dhe 600 s për hard. Daljet e plota (fronti, 20 vektorët) janë te dosja [results/](results/).

### Hypervolume i 20 vektorëve të zgjedhur (i normalizuar, sa më i madh aq më mirë)

| Instanca | Random | Minimum degree | **Simulated Annealing** | Iterated Local Search |
|---|---|---|---|---|
| easy | 0.632 | 0.960 | **0.967** | 0.964 |
| medium | 0.171 | 0.486 | **0.531** | 0.489 |
| hard | 0.098 | 0.101 | **0.239** | 0.210 |

Te easy diferencat duken të vogla, sepse gjerësitë janë ≤ 20 kurse referenca është 501. Tabela e mëposhtme e tregon dallimin më qartë.

### Torso më e madhe me gjerësi ≤ k (nga 20 vektorët e zgjedhur)

| Instanca | k | Minimum degree | **SA** | ILS |
|---|---|---|---|---|
| easy | 19 | 20 | 340 | **1,013** |
| easy | 15 | 16 | **317** | 227 |
| easy | 10 | 11 | **287** | 91 |
| easy | 5 | 6 | **186** | 44 |
| medium | 250 | 251 | **449** | 260 |
| medium | 200 | 201 | **374** | 208 |
| medium | 100 | 101 | **154** | 89 |
| hard | 450 | 451 | **1,909** | 1,642 |
| hard | 400 | 401 | **1,237** | 941 |
| hard | 350 | 351 | **664** | 328 |

### Çka tregojnë rezultatet

- **Random** është shumë larg, sepse fill-in-i i një renditjeje të rastësishme e bën grafin shumë të dendur (gjerësia e plotë 199 te easy, 930 te medium).
- **Minimum degree** jep gjerësinë më të vogël për **të gjithë grafin**, por fronti i saj është trivial: me gjerësi `k` arrihet vetëm torso me `k + 1` nyje, sepse nyjet më të dendura mbeten në fund.
- **SA** është më e mira në të tria instancat. Te easy, me gjerësi 10 gjen torso me **287 nyje** në vend të 11. Te hard, me gjerësi 450 gjen torso me **1,909 nyje** në vend të 451.
- **ILS** gjen ndonjëherë një pikë shumë të mirë: te easy torso me **1,013 nyje** me gjerësi 19. Por ngec më shpesh në minimume lokale, sepse pranon vetëm lëvizje që nuk e përkeqësojnë zgjidhjen. SA, që pranon edhe lëvizje më të këqija, eksploron më mirë.
- **Hard** është më i kufizuari nga koha: një vlerësim zgjat ~70 ms, prandaj për çdo `k` bëhen vetëm ~450 iteracione. Me më shumë kohë fronti do të përmirësohej.
- Meqë dorëzohen vetëm 20 vektorë, disa pika të ndërmjetme janë më të dobëta se te minimum degree. P.sh. te hard me `k = 300`, SA ka 283 nyje kundrejt 301. Kjo ndodh sepse zgjedhja greedy i jep përparësi pikave që e rrisin HV më shumë.

## 7. Ekzekutimi

Kërkohet Python 3.10+ (për `int.bit_count`) dhe nuk ka nevojë për librari të jashtme.

```bash
cd task4

# Kontrollo shembullin e detyres (torso size 4, width 2)
python main.py --example

# Baseline: renditja minimum degree ose e rastesishme
python main.py easy -m mindeg
python main.py easy -m random

# Metaheuristikat (koha ne sekonda)
python main.py easy -m sa --time 300
python main.py medium -m ils --time 300

# Ruaj 20 vektoret ne formatin JSON te dorezimit ne ESA
python main.py hard -m sa --time 600 --out results/hard_sa.json
```

Opsionet: `-m sa|ils|mindeg|random`, `--time`, `--seed`, `--targets` (sa gjerësi `k` optimizohen), `--out`.

Formati i dorezimit (`--out`), sipas README-së së ESA:

```json
[{"decisionVector": [[p1, ..., pn, t], ...], "problem": "small-graph", "challenge": "spoc-3-torso-decompositions"}]
```
