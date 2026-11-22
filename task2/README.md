# Detyra 2 – Vendosja e mysafirëve në tavolina me SAT

**SAT Problems**

## 1. Përshkrimi i problemit

Në një aheng janë ftuar **100 mysafirë**, të cilët duhet të ulen në **10 tavolina** me nga **10 karrige**. Kushtet janë:

1. Ciftet në listën e **konflikteve** nuk mund të ulen në të njëjtën tavolinë (p.sh. `(M1, M5)`).
2. Në çdo tavolinë, dallimi mes numrit të **burrave** dhe të **grave** nuk mund të jetë më i madh se **±3**.
3. Mysafirët në listën **bashkë** duhet të ulen në të njëjtën tavolinë.

**Kërkesa:** të definohet formula SAT për zgjidhjen e problemit. Përveç formulës, programi e ndërton atë automatikisht në CNF, e zgjidh me një SAT solver CDCL të shkruar nga e para dhe e verifikon zgjidhjen.

## 2. Çka është SAT

**SAT** (Boolean Satisfiability) pyet: *a ekziston një caktim i vlerave true/false për variablat që e bën formulën të vërtetë?*

Formula shkruhet në **CNF** (Conjunctive Normal Form):

- **literal**: një variabël `x` ose mohimi i saj `¬x`;
- **klauzolë**: disjunksion (OSE) literalesh, p.sh. `(¬x₁ ∨ x₂ ∨ x₃)`. Është e vërtetë nëse **të paktën një** literal është i vërtetë;
- **formula CNF**: konjuksion (DHE) klauzolash. Është e vërtetë nëse **çdo** klauzolë është e vërtetë.

## 3. Variablat

```
x(g, t) = true   ⇔   mysafiri g ulet në tavolinën t        g = 1..100,  t = 1..10
```

Gjithsej janë **100 × 10 = 1000 variabla** kryesore. Çdo caktim i tyre përshkruan një vendosje të mysafirëve; formula e detyron që vendosja të jetë valide.

## 4. Formula SAT

Shënime: `G` = mysafirët, `T` = tavolinat, `S = 10` karriget për tavolinë, `D = 3`, `K` = lista e konflikteve, `B` = burrat, `Gr` = gratë.

### (1) Çdo mysafir ulet në saktësisht një tavolinë

```
(1a)  ∧_{g ∈ G}  ( x(g,1) ∨ x(g,2) ∨ … ∨ x(g,10) )                    të paktën një
(1b)  ∧_{g ∈ G} ∧_{t < t'}  ( ¬x(g,t) ∨ ¬x(g,t') )                     të shumtën një
```

(1a) jep 100 klauzola. (1b) jep 100 × 45 = 4,500 klauzola: për çdo çift tavolinash, mysafiri nuk mund të jetë në të dyja.

### (2) Në çdo tavolinë ulen të shumtën 10 mysafirë

```
(2)   ∧_{t ∈ T}  ( Σ_g x(g,t) ≤ 10 )
```

Mjafton "të shumtën 10". Me (1) çdo mysafir zë saktësisht një karrige, gjithsej 100. Nëse ndonjë tavolinë do të kishte më pak se 10, të tjerat do të duhej të kishin më shumë se 10, gjë që (2) e ndalon. Pra çdo tavolinë ka **saktësisht 10**.

Kushti `Σ ≤ k` nuk është klauzolë, prandaj kodohet në CNF me numëruesin sekuencial (seksioni 5).

### (3) Konfliktet

```
(3)   ∧_{(a,b) ∈ K} ∧_{t ∈ T}  ( ¬x(a,t) ∨ ¬x(b,t) )
```

Për çdo tavolinë, të paktën njëri nga `a` dhe `b` nuk ulet aty. Shembulli i detyrës `(M1, M5)` jep 10 klauzola: `(¬x(M1,t) ∨ ¬x(M5,t))` për `t = 1..10`.

### (4) Mysafirët që ulen bashkë

Për një grup `{a, b, c}` mjafton që anëtarët e njëpasnjëshëm të jenë në të njëjtën tavolinë: `a` me `b` dhe `b` me `c`.

```
(4)   ∧_{grupet} ∧_{(a,b) njëpasnjëshëm} ∧_{t ∈ T}  ( x(a,t) ↔ x(b,t) )

      x(a,t) ↔ x(b,t)   =   ( ¬x(a,t) ∨ x(b,t) ) ∧ ( ¬x(b,t) ∨ x(a,t) )
```

### (5) Gjinia: |burra − gra| ≤ 3

Në një tavolinë me 10 karrige, `nB + nG = 10`, pra `nB − nG = 2·nB − 10`:

```
−3 ≤ 2·nB − 10 ≤ 3   ⇒   3.5 ≤ nB ≤ 6.5   ⇒   4 ≤ nB ≤ 6   (dhe 4 ≤ nG ≤ 6)
```

`nB ≥ 4` është e njëjta gjë si `nG ≤ 6`. Prandaj kushti shkruhet me dy kufizime "të shumtën":

```
(5)   ∧_{t ∈ T}  ( Σ_{g ∈ B} x(g,t) ≤ 6 )  ∧  ( Σ_{g ∈ Gr} x(g,t) ≤ 6 )
```

Në përgjithësi, kufiri është `⌊(S + D)/2⌋`, te funksioni `gender_bounds()`. Kjo vlen kur tavolinat janë plot, siç është rasti me 100 mysafirë në 10 × 10 karrige.

### Formula e plotë

```
F  =  (1a) ∧ (1b) ∧ (2) ∧ (3) ∧ (4) ∧ (5)
```

- **F është e plotësueshme (SAT)** atëherë dhe vetëm atëherë kur ekziston një vendosje që i plotëson të gjitha kushtet.
- Nga modeli lexohet vendosja: mysafiri `g` ulet në tavolinën `t` për të cilën `x(g,t) = true`.

## 5. Kodimi i "të shumtën k" në CNF: numëruesi sekuencial

Kushti `x₁ + x₂ + … + xₙ ≤ k` kodohet me numëruesin sekuencial (Sinz, 2005). Për të shtohen variabla ndihmëse:

```
s(i, j) = true  ⇒  ndër x₁ … xᵢ janë të vërteta të paktën j
```

Klauzolat (për `1 < i < n`, `1 < j ≤ k`):

```
¬x₁ ∨ s(1,1)                               x₁ e rrit numëruesin në 1
¬s(1,j)                                    në fillim numëruesi s'mund të jetë > 1
¬xᵢ ∨ s(i,1)                               xᵢ e vërtetë → të paktën 1
¬s(i−1,j) ∨ s(i,j)                         numëruesi nuk zvogëlohet
¬xᵢ ∨ ¬s(i−1,j−1) ∨ s(i,j)                 xᵢ e vërtetë → numëruesi rritet me 1
¬xᵢ ∨ ¬s(i−1,k)                            nëse ishin k, xᵢ nuk mund të jetë e vërtetë
¬xₙ ∨ ¬s(n−1,k)
```

Kodimi shton `(n−1)·k` variabla dhe rreth `2·n·k` klauzola. Kodimi "naiv" do të ndalonte çdo nëngrup me `k+1` elemente: për tavolinat do të ishin `C(100, 11) ≈ 1.4·10¹⁴` klauzola, gjë që është e pamundur.

Implementimi gjendet te `at_most()` në [seating_sat.py](seating_sat.py).

### Thyerja e simetrisë

Tavolinat janë identike: çdo zgjidhje mund të përkthehet në 10! = 3,628,800 zgjidhje të tjera, vetëm duke ua ndërruar numrat tavolinave. Prandaj shtohet klauzola `(x(M1, 1))`: mysafiri i parë ulet në tavolinën 1. Kjo nuk humb asnjë zgjidhje. Mund të çaktivizohet me `--no-symmetry`.

## 6. Madhësia e formulës (instanca `aheng`)

| Kushti | Klauzola | Variabla ndihmëse |
|---|---|---|
| (1a) të paktën një tavolinë | 100 | – |
| (1b) të shumtën një tavolinë | 4,500 | – |
| (2) kapaciteti i tavolinës | 20,690 | 9,900 |
| (3) konfliktet (150 çifte) | 1,500 | – |
| (4) bashkë (12 grupe) | 540 | – |
| (5) gjinia, burra / gra | 6,570 / 6,050 | 3,060 / 2,820 |
| simetria | 1 | – |
| **Gjithsej** | **39,951** | **1,000 x(g,t) + 15,780 = 16,780 variabla** |

Me `--formula` shfaqen klauzolat e çdo kushti me emrat e variablave, p.sh. `(~x(M1,T1) v ~x(M5,T1))`. Me `--dimacs file.cnf` formula ruhet në formatin standard DIMACS dhe mund të jepet edhe te solver-ë të tjerë (MiniSat, Glucose, …).

## 7. SAT solver-i: CDCL

Solver-i në [sat_solver.py](sat_solver.py) është **CDCL** (Conflict-Driven Clause Learning), algoritmi që përdorin solver-ët modernë:

```
CDCL(F):
    përderisa true:
        konflikt ← UNIT_PROPAGATION()          (klauzolat me 1 literal të mbetur detyrojnë vlerën)
        nëse ka konflikt:
            nëse niveli = 0 → kthe UNSAT
            klauzola ← ANALIZO(konflikt)        (1-UIP: shkaku i konfliktit)
            shto klauzolën në F                 (clause learning)
            BACKJUMP te niveli i duhur          (backtracking jo-kronologjik)
        përndryshe:
            nëse të gjitha variablat kanë vlerë → kthe SAT dhe modelin
            zgjidh një variabël (VSIDS) dhe jepi vlerë   (vendim)
```

- **Unit propagation me two watched literals:** për çdo klauzolë vëzhgohen vetëm 2 literale, kështu që propagimi nuk i kalon të gjitha klauzolat.
- **Clause learning:** pas çdo konflikti mësohet një klauzolë e re, që e ndalon të njëjtin gabim në të ardhmen.
- **VSIDS:** zgjidhen variablat që marrin pjesë më shpesh në konflikte.
- **Phase saving** dhe **restarte Luby:** pas një restarti, solver-i rifillon me vlerat e fundit të variablave.
- Me konflikt në nivelin 0 (pa asnjë vendim), formula është **UNSAT**. Kjo është vërtetim që vendosja nuk ekziston.

Solver-i është testuar me 400 formula të rastësishme kundrejt kërkimit të plotë (brute force), dhe rezultati përputhet në të gjitha rastet.

## 8. Verifikimi

Pas zgjidhjes, programi bën dy kontrolle të pavarura:

1. **Formula e plotësuar = True:** çdo klauzolë ka të paktën një literal të vërtetë (`check_model`).
2. **Objective function `violations()`:** numëron kushtet e shkelura direkt nga vendosja, pa formulën. Kontrollon:
   - a ka mysafirë pa tavolinë ose në dy tavolina;
   - tavolina me më shumë se 10 mysafirë;
   - `|B − G| > 3`;
   - çifte konflikti bashkë;
   - grupe të ndara.

   `kushte të shkelura = 0` do të thotë që vendosja është valide.

## 9. Rezultatet

| Instanca | Mysafirë | Konflikte | Grupe bashkë | Rezultati | Konflikte CDCL | Koha |
|---|---|---|---|---|---|---|
| `shembull` | 12 (3 × 4, D = 2) | 5 | 2 | SAT ✔ | 3 | < 0.01 s |
| `aheng` | 100 (10 × 10, D = 3) | 150 | 12 | SAT ✔ | 1,440 | ~4–5 s |
| `aheng-i-veshtire` | 100 (10 × 10, D = 3) | 600 | 20 | SAT ✔ | 13 | ~0.1 s |
| `unsat-grupi` | 100 | 151 | 12 | UNSAT | 18 | 0.02 s |
| `unsat-gjinia` | 30 (3 × 10), 19 burra | 30 | 2 | UNSAT | 252 | 0.25 s |

- Te instancat SAT, të gjitha vendosjet kanë `valid = True`, dhe çdo tavolinë ka 4–6 burra.
- `unsat-grupi`: dy anëtarë të të njëjtit grup janë në konflikt. Propagimi e gjen kontradiktën pas 18 konflikteve.
- `unsat-gjinia`: në 3 tavolina hyjnë të shumtën 3 × 6 = 18 burra, por janë 19.
- **Kufizimi i SAT-it:** për 100 mysafirë me 64 burra (maksimumi 60), solver-i nuk e vërteton UNSAT brenda 180 s. Kjo është e njohur: provat e tipit **pigeonhole** ("64 burra në 60 vende") kërkojnë rezolucion eksponencial. Prandaj programi bën edhe një **kontroll paraprak** me numërim (`quick_checks()`), që e zbulon menjëherë.

Shembull i daljes (`aheng`):

```
Tavolina  1 [10 | B=6 G=4]: M1(B) M9(B) M41(B) M50(G) M56(B) M58(G) M60(G) M70(B) M77(G) M99(B)
Tavolina  2 [10 | B=6 G=4]: M24(B) M59(B) M72(B) M76(B) M79(B) M87(G) M93(G) M96(G) M98(G) M100(B)
...
Tavolina 10 [10 | B=5 G=5]: M14(B) M20(B) M33(G) M40(B) M45(B) M48(G) M54(G) M82(G) M90(G) M95(B)

Formula e plotesuar = True | kushte te shkelura = 0 | valid = True
```

## 10. Ekzekutimi

Kërkohet Python 3.8+ dhe nuk ka nevojë për librari të jashtme.

```bash
cd task2

# Instanca e detyres (100 mysafire, 10 tavolina)
python seating_sat.py

# Instancat e gatshme
python seating_sat.py --list
python seating_sat.py unsat-grupi

# Shfaq klauzolat e formules sipas kushteve
python seating_sat.py shembull --formula

# Ruaj formulen ne formatin DIMACS
python seating_sat.py aheng --dimacs aheng.cnf

# Instance nga skedari tekstual
python seating_sat.py instanca.txt

# Ruaj instancat si skedare .txt
python instances.py --write instances
```

Formati tekstual i instancës:

```
tables 10 10            # 10 tavolina me 10 karrige
diff 3                  # |burra - gra| <= 3
guest M1 B              # emri dhe gjinia (B = burre, G = grua)
guest M5 G
conflict M1 M5          # M1 dhe M5 nuk ulen bashke
together M2 M7 M9       # M2, M7, M9 ulen ne te njejten tavoline
```
