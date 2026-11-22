# Detyra 3 – Killer Sudoku me Constraint Programming (CSP)

**Constraint Programming Problem**

## 1. Përshkrimi i problemit

Killer Sudoku është një variant i Sudoku-s ([sudoku.com/killer](https://sudoku.com/killer)):

- rrjeta 9×9 mbushet me numrat 1–9;
- çdo **rresht**, **kolonë** dhe **kuti 3×3** ka numrat 1–9 pa përsëritje;
- rrjeta është e ndarë në **kafaze** (cages), d.m.th. grupe qelizash të lidhura. Për secilin jepet **shuma** e numrave brenda tij, dhe brenda kafazit numrat **nuk përsëriten**.

Ndryshe nga Sudoku klasik, **nuk ka numra të dhënë**. I gjithë informacioni vjen nga kafazet dhe shumat e tyre.

## 2. Modelimi si CSP

Një CSP (Constraint Satisfaction Problem) përbëhet nga **(X, D, C)**:

| Elementi | Në këtë problem |
|---|---|
| **X: variablat** | 81 qelizat e rrjetës |
| **D: domain-i** | `{1, …, 9}` për çdo qelizë |
| **C: kufizimet** | 27 kufizime **all-different** (9 rreshta, 9 kolona, 9 kuti) + për çdo kafaz: **all-different** dhe **sum = shuma e kafazit** |

**Kufizimet e kafazeve:**

```
për kafazin K me qelizat q₁ … qₖ dhe shumën s:
    all-different(q₁, …, qₖ)
    q₁ + q₂ + … + qₖ = s
```

**Testi i qëllimit:** çdo qelizë ka vlerë dhe asnjë kufizim nuk shkelet.

Kontroll i shpejtë: shuma e të gjitha kafazeve duhet të jetë **405 = 9 × 45**, sepse çdo rresht ka shumën 1 + … + 9 = 45.

## 3. Reprezentimi

- **Domain-et** ruhen si **bitmask**: biti `v` është 1 nëse vlera `v` është ende e mundshme. `ALL = 0b1111111110` do të thotë {1, …, 9}.
- **Fqinjët** e një qelize janë qelizat që duhet të kenë vlerë tjetër: rreshti, kolona, kutia **dhe** kafazi i saj. Janë të llogaritur paraprakisht në `peers`.
- **`COMBOS[(k, s)]`**: të gjitha kombinimet e `k` numrave të ndryshëm 1–9 me shumë `s`, të llogaritura një herë në fillim. Shembuj:

| Kafazi | Kombinimet | Domain-i i qelizave |
|---|---|---|
| 2 qeliza, shuma 3 | {1,2} | {1, 2} |
| 2 qeliza, shuma 17 | {8,9} | {8, 9} |
| 3 qeliza, shuma 6 | {1,2,3} | {1, 2, 3} |
| 3 qeliza, shuma 24 | {7,8,9} | {7, 8, 9} |
| 2 qeliza, shuma 10 | {1,9} {2,8} {3,7} {4,6} | {1,2,3,4,6,7,8,9}: 5 nuk lejohet, sepse 5+5 përsëritet |

- **Formati i enigmës:** 9 rreshta me 9 simbole, ku qelizat me të njëjtin simbol janë në të njëjtin kafaz, dhe pastaj shumat. Shembull te [puzzles.py](puzzles.py):

```
onBBBGFFy
nnBbqqqFy
...
a=22 b=15 c=11 ...
```

## 4. Objective function

```
f(S) = Σ_{27 njësitë} (9 − |vlerat e ndryshme|)
     + Σ_{kafazet} (përsëritjet në kafaz + [shuma ≠ s])
```

- `f(S) = 0` atëherë dhe vetëm atëherë kur rrjeta është zgjidhje.
- Pas çdo zgjidhjeje, programi shtyp `Kufizime të shkelura = 0 | valid = True`.

Implementimi gjendet te `violations()` në [killer_sudoku.py](killer_sudoku.py).

## 5. Constraint propagation

Thelbi i Constraint Programming është që kufizimet të **zvogëlojnë domain-et para dhe gjatë kërkimit**. Propagimi (`_propagate`) përsërit tri rregulla derisa asnjë domain të mos ndryshojë më, pra deri në **pikë fikse**:

1. **Eliminimi nga fqinjët (naked single).** Kur një qelizë ka vetëm një vlerë, ajo vlerë largohet nga domain-et e të gjithë fqinjëve (rresht, kolonë, kuti, kafaz). Kjo është **arc consistency** për kufizimet `≠`.
2. **Kombinimet e kafazeve** (`_cage_filter`). Për çdo kafaz mbahen vetëm kombinimet që:
   - kanë shumën e mbetur të duhur,
   - nuk përdorin numra që janë tashmë në kafaz,
   - mund të vendosen në domain-et e qelizave të mbetura.

   Domain-i i çdo qelize kufizohet në bashkimin e këtyre kombinimeve. Kjo është **generalized arc consistency** për kufizimin e shumës.
3. **Hidden single.** Nëse në një njësi (rresht, kolonë, kuti) një numër mund të shkojë vetëm në një qelizë, ajo qelizë e merr atë numër. Nëse nuk mund të shkojë askund, kemi **kontradiktë**.

Nëse ndonjë domain bëhet bosh, kemi **kontradiktë**, dhe dega pritet (backtrack).

**Shembull:** një kafaz me 2 qeliza dhe shumë 4 ka vetëm kombinimin {1,3}, prandaj domain-et e të dyja qelizave bëhen {1,3}. Nëse në rreshtin e njërës prej tyre ndodhet një kafaz me 1 qelizë dhe shumë 1, numri 1 largohet nga ai rresht. Atëherë ajo qelizë merr 3, dhe qeliza tjetër e kafazit merr 1. Te shumica e enigmave, vetëm propagimi në fillim e zgjidh pjesën më të madhe të rrjetës.

## 6. Kërkimi: backtracking me MRV

Kur propagimi ndalet dhe ende ka qeliza me më shumë se një vlerë, nevojitet kërkimi:

```
SEARCH(domain-et):
    nëse çdo qelizë ka 1 vlerë → kthe zgjidhjen
    q ← qeliza me më pak vlera të mundshme          (MRV)
    për çdo vlerë v në domain-in e q:
        D' ← domain-et me q = v
        D' ← PROPAGATE(D')                          (ose vetëm forward checking)
        nëse s'ka kontradiktë dhe SEARCH(D') gjen zgjidhje → kthe atë
    BACKTRACK                                        (asnjë vlerë s'funksionoi)
```

Për krahasim janë implementuar **tri metoda**:

| Metoda | Zgjedhja e qelizës | Kontrolli pas çdo vlere |
|---|---|---|
| `bt`: backtracking i thjeshtë | me radhë A1, A2, … | vetëm a shkel vlera kufizimet me qelizat e mbushura (shuma e pjesshme < s) |
| `fc`: forward checking + MRV | MRV | vlera largohet nga domain-et e fqinjëve, dhe kafazi i qelizës filtrohet sipas kombinimeve |
| `full`: MRV + propagim i plotë | MRV | propagim i plotë deri në pikë fikse (seksioni 5) |

## 7. Enigmat

Enigmat te [puzzles.py](puzzles.py) janë gjeneruar me [generator.py](generator.py):

1. Gjenerohet një rrjetë e plotë valide Sudoku, me renditje të rastësishme.
2. Rrjeta ndahet në kafaze të lidhura, pa numër të përsëritur brenda kafazit.
3. Shuma e çdo kafazi llogaritet nga rrjeta.
4. Me solver-in CSP kërkohen **deri në 2 zgjidhje**. Nëse ka 2, kafazi i një qelize ku ato dallojnë ndahet, dhe kontrolli përsëritet derisa **zgjidhja të jetë unike**.

| Niveli | Madhësia fillestare e kafazeve | Enigmat |
|---|---|---|
| Easy | 1–3 qeliza | easy-1 (47 kafaze), easy-2 (52) |
| Medium | 2–4 qeliza | medium-1 (34), medium-2 (37) |
| Hard | 2–5 qeliza | hard-1 (31), hard-2 (36) |
| Expert | 3–6 qeliza | expert-1 (27), expert-2 (31) |

Sa më të mëdhenj kafazet, aq më shumë kombinime ka secili, dhe aq më pak informacion jep. Unikaliteti kontrollohet me `python killer_sudoku.py <enigma> --unique`.

## 8. Rezultatet

Rezultatet merren me `python compare.py` (kufiri: 2,000,000 nyje dhe 60 s; për `bt` te hard-1 dhe expert-1 kufiri është rritur).

| Enigma | `bt` nyje | `bt` koha | `fc` nyje | `fc` koha | `full` nyje | `full` koha |
|---|---|---|---|---|---|---|
| easy-1 | 2,075 | 0.01 s | 87 | 0.002 s | **1** | 0.001 s |
| easy-2 | 1,874 | 0.01 s | 129 | 0.002 s | **1** | 0.001 s |
| medium-1 | 159,683 | 0.9 s | 168 | 0.003 s | **3** | 0.006 s |
| medium-2 | 113,289 | 0.6 s | 228 | 0.004 s | **1** | 0.002 s |
| hard-1 | 2,558,426 | 14.3 s | 3,483 | 0.05 s | **6** | 0.009 s |
| hard-2 | 9,844 | 0.05 s | 87 | 0.002 s | **1** | 0.002 s |
| expert-1 | 2,561,722 | 13.3 s | 6,445 | 0.12 s | **16** | 0.02 s |
| expert-2 | 1,354,691 | 7.4 s | 846 | 0.01 s | **9** | 0.01 s |

Të gjitha zgjidhjet kanë `valid = True`.

- **`bt`** nuk përdor domain-e. Një gabim zbulohet vetëm kur arrihet qeliza që e shkel kufizimin, prandaj nevojiten deri në 2.5 milionë nyje.
- **`fc`** e zvogëlon numrin e nyjeve 15–1,600 herë: vlerat e pamundshme largohen menjëherë, dhe MRV zgjedh qelizën më të kufizuar.
- **`full`**: propagimi i plotë **i zgjidh enigmat easy, medium-2 dhe hard-2 pa asnjë vendim** (1 nyje = vetëm rrënja). Për të tjerat mjaftojnë 3–16 nyje. Kjo është ideja e Constraint Programming: sa më shumë punë bëjnë kufizimet, aq më pak kërkim nevojitet.
- Te enigmat expert, kafazet e mëdha kanë shumë kombinime, prandaj propagimi ndalet më herët dhe nevojitet pak kërkim me backtracking.

Shembull (`easy-1`): harta e kafazeve dhe zgjidhja.

```
a a b | b b c | c d e          6 8 3 | 2 9 5 | 4 1 7
f f g | h h i | j j e          4 2 1 | 8 6 7 | 3 5 9
k l m | n n o | j p q          7 9 5 | 3 4 1 | 8 6 2
------+-------+------          ------+-------+------
r s s | t t o | u v v          5 7 2 | 1 3 4 | 9 8 6
w w x | x y y | z z z          8 4 6 | 5 7 9 | 1 2 3
A B x | C D E | F F F          3 1 9 | 6 8 2 | 5 7 4
------+-------+------          ------+-------+------
G B H | D D I | J K L          1 3 8 | 4 2 6 | 7 9 5
G B M | N O O | K K P          9 6 4 | 7 5 8 | 2 3 1
Q R R | S T T | U P P          2 5 7 | 9 1 3 | 6 4 8
a=14 b=14 c=9 d=1 e=16 ...
```

## 9. Ekzekutimi

Kërkohet Python 3.8+ dhe nuk ka nevojë për librari të jashtme.

```bash
cd task3

# Zgjidh nje enigme (default: easy-1, metoda full)
python killer_sudoku.py
python killer_sudoku.py expert-1

# Enigmat e gatshme
python killer_sudoku.py --list

# Zgjidh metoden: bt, fc ose full
python killer_sudoku.py hard-1 -m fc

# Kontrollo nese zgjidhja eshte unike
python killer_sudoku.py medium-1 --unique

# Enigme nga skedari (harta 9x9 + shumat)
python killer_sudoku.py enigma.txt

# Krahasimi i metodave ne te gjitha enigmat
python compare.py
python compare.py hard-1 expert-1 -m fc full

# Gjenero enigme te re me zgjidhje unike
python generator.py --level hard --seed 5
```
