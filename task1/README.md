# Detyra 1 – Blocked N-Queens me A*

**Teknikat e informuara të kërkimit (Informed Search Techniques)**

## 1. Përshkrimi i problemit

Blocked N-Queens është një variant i problemit N-Queens. Kemi një tabelë **N×N** dhe **N mbretëresha**. Disa katrorë të tabelës janë **të bllokuar**, dhe në to nuk mund të vendoset mbretëreshë. Qëllimi është të vendosen të N mbretëreshat në katrorë jo të bllokuar, ashtu që asnjë çift mbretëreshash të mos jetë në të njëjtin **rresht**, **kolonë** ose **diagonale** ([përshkrimi në ASP Competition](https://dtai.cs.kuleuven.be/events/ASP-competition/Benchmarks/BlockedQueens.shtml)).

**Formati i hyrjes** (si në ASP Competition):

```
num(1). num(2). num(3). num(4). block(1,1). block(2,2). block(4,3).
```

**Formati i daljes:** `queen(i,j)` do të thotë që ka mbretëreshë në rreshtin `i` dhe kolonën `j`.

```
queen(1,3). queen(2,1). queen(3,4). queen(4,2).
```

Për shembullin e mësipërm, programi jep pikërisht zgjidhjen që tregohet në faqen e ASP Competition.

## 2. Modelimi i problemit

| Elementi | Në këtë problem |
|---|---|
| **Gjendja** | Mbretëreshat e vendosura deri tani (të shumtën një për rresht) dhe, për çdo rresht të mbetur, kolonat ende të lira |
| **Gjendja fillestare** | Tabela pa asnjë mbretëreshë |
| **Veprimi (operatori)** | Vendos një mbretëreshë në një katror të lirë të një rreshti të mbetur |
| **Testi i qëllimit** | Janë vendosur të N mbretëreshat |
| **Kostoja** | Çdo veprim kushton 1, pra `g(n) = k` (numri i mbretëreshave). Çdo zgjidhje ka kosto **N** |

### Kufizimet

1. Mbretëreshat nuk vendosen në katrorë **të bllokuar**.
2. Në çdo **rresht** ka saktësisht një mbretëreshë (N mbretëresha në N rreshta).
3. Në çdo **kolonë** ka të shumtën një mbretëreshë.
4. Në çdo **diagonale** (të dy drejtimet) ka të shumtën një mbretëreshë.

Kufizimet 1 dhe 2 respektohen nga vetë modelimi: në çdo hap mbushet një rresht i ri dhe provohen vetëm katrorët e lirë. Kufizimet 3 dhe 4 respektohen me forward checking (shih seksionin 3).

### Cili rresht mbushet?

- **`row`:** rreshtat mbushen me radhë: 1, 2, …, N.
- **`mrv`** (default): mbushet rreshti me **më së paku katrorë të lirë** (Minimum Remaining Values). Kështu konfliktet zbulohen më herët.

Në të dy rastet, rreshti që mbushet në një gjendje është i përcaktuar. Prandaj një gjendje arrihet vetëm nga një rrugë: pema e kërkimit **nuk ka gjendje të përsëritura** dhe nuk nevojitet closed list.

## 3. Reprezentimi

- **Gjendja** është një tuple `(queens, avail)`:
  - `queens`: ciftet `(rreshti, kolona)` të mbretëreshave të vendosura.
  - `avail`: për çdo rresht të mbetur, një **bitmask** me kolonat ende të lira. Biti `c` është 1 nëse kolona `c` nuk është as e bllokuar, as e sulmuar.
- **Forward checking:** kur vendoset mbretëresha në `(r0, c)`, për çdo rresht tjetër `r` me distancë `d = |r − r0|` largohen tri kolona:

  ```
  c        (kolona)
  c − d    (diagonalja e majtë)
  c + d    (diagonalja e djathtë)
  ```

  Në kod kjo bëhet me një veprim të vetëm: `m & ~(bit | bit << d | bit >> d)`.
- **Open list:** priority queue (`heapq`) me çelësin `(f, −g, tie, numëruesi)`.

## 4. Objective function

```
conflicts(S) = (çifte mbretëreshash që sulmojnë njëra-tjetrën) + (mbretëresha në katrorë të bllokuar)
```

- `conflicts(S) = 0` vlen atëherë dhe vetëm atëherë kur `S` është zgjidhje valide.
- Pas çdo zgjidhjeje, programi shtyp `Konflikte = 0 | valid = True` si verifikim.

Implementimi gjendet te `conflicts()` në [blocked_queens.py](blocked_queens.py).

## 5. Algoritmi A*

A* zgjeron gjithmonë nyjen me vlerën më të vogël të `f(n) = g(n) + h(n)`:
- `g(n)` = kostoja deri te nyja (sa mbretëresha janë vendosur);
- `h(n)` = vlerësimi i kostos së mbetur deri te qëllimi (heuristika).

```
A*(tabela, h):
    open ← priority queue me gjendjen fillestare
    përderisa open nuk është bosh:
        n ← nyja me f më të vogël           (barazimet: g më i madh, pastaj tie)
        nëse n ka N mbretëresha → kthe n     (qëllimi)
        për çdo katror të lirë në rreshtin e zgjedhur:
            n' ← n + mbretëreshë në atë katror
            nëse h(n') = ∞ → prite degën      (dead end, backtracking)
            përndryshe → shto n' në open me f = g + 1 + h(n')
    kthe "nuk ka zgjidhje"
```

**Pse renditet sipas g kur f është i barabartë?** Te ky problem kostoja e vërtetë e mbetur për një gjendje të zgjidhshme është saktësisht `h* = N − k`. Prandaj me një heuristikë admissible shumë nyje kanë të njëjtin `f = N`. Nëse barazimi zgjidhet në favor të nyjes më të thellë, A* shkon drejt zgjidhjes dhe nuk i hap të gjitha nivelet si BFS.

**Kur kthen "nuk ka zgjidhje"?** Kur open list zbrazet. Me heuristikë admissible kjo është **vërtetim** që problemi nuk ka zgjidhje, sepse asnjë degë e zgjidhshme nuk pritet.

## 6. Heuristikat

Kostoja e vërtetë e mbetur është:
- `h*(n) = N − k` nëse nga gjendja `n` mund të arrihet zgjidhja;
- `h*(n) = ∞` nëse nuk mund të arrihet (dead end).

Një heuristikë është **admissible** kur `h(n) ≤ h*(n)` për çdo nyje, d.m.th. kur nuk e mbivlerëson kurrë koston.

| | Heuristika | Formula | Admissible? |
|---|---|---|---|
| **H1** | Rreshtat e mbetur | `h = N − k` | **Po**: `N − k ≤ h*` gjithmonë |
| **H2** | Forward checking | `h = ∞` nëse ndonjë rresht i mbetur s'ka katror të lirë, përndryshe `N − k` | **Po**: `∞` jepet vetëm kur dega me siguri s'ka zgjidhje |
| **H3** | MRV | `h = (N − k) + Σ 1/|avail(r)|` mbi rreshtat e mbetur (`∞` nëse ndonjë është 0) | **Jo**: për çdo gjendje të zgjidhshme `h > N − k = h*` |

- **H1** është heuristika më e thjeshtë. Nuk i dallon gjendjet e mira nga ato pa dalje: një dead end zbulohet vetëm kur arrihet rreshti pa katrorë të lirë.
- **H2** e kontrollon këtë që më herët: sapo një rresht mbetet pa katrorë të lirë, dega pritet.
- **H3** përpiqet të dallojë gjendjet: rreshtat me pak opsione e rrisin `h`. Kjo e mbivlerëson koston.

Implementimi gjendet te `h_rows()`, `h_forward()` dhe `h_mrv()` në [blocked_queens.py](blocked_queens.py).

## 7. Rezultatet

Rezultatet merren me `python compare.py`, me kufi prej 100,000 nyjesh të zgjeruara dhe 20 s për çdo ekzekutim. Instancat janë te [instances.py](instances.py): shembulli i ASP Competition, një instancë e vogël pa zgjidhje (`unsat6`) dhe tabela të gjeneruara me seed fiks, ku `pY` është përqindja e katrorëve të bllokuar.

### Rreshtat me radhë (`--order row`): nyje të zgjeruara

| Instanca | N | Të bllokuar | H1 | H2 | H3 | **H4** |
|---|---|---|---|---|---|---|
| example | 4 | 3 | 7 | 6 | 4 | **4** |
| unsat6 (pa zgjidhje) | 6 | 6 | 21 | 11 | 11 | **9** |
| n8-p10 | 8 | 6 | 90 | 40 | 114 | **42** |
| n16-p40 | 16 | 102 | 13,443 | 3,991 | 10,077 | **46** |
| n16-p60 (pa zgjidhje) | 16 | 154 | 30,932 | 7,157 | 7,157 | **2,837** |
| n24-p50 | 24 | 288 | > 100,000 | > 100,000 | > 100,000 | **854** |
| n32-p55 | 32 | 563 | > 100,000 | > 100,000 | timeout | **30,352** |
| n48-p50 | 48 | 1,152 | > 100,000 | > 100,000 | timeout | **18,757** |
| n64-p50 | 64 | 2,048 | > 100,000 | > 100,000 | timeout | > 100,000 |

### Rreshti me MRV (`--order mrv`, default): nyje të zgjeruara

| Instanca | H1 | H2 | H3 | **H4** | Koha e H4 |
|---|---|---|---|---|---|
| example | 7 | 6 | 4 | **4** | < 0.01 s |
| unsat6 (pa zgjidhje) | 17 | 11 | 11 | **9** | < 0.01 s |
| n8-p10 | 21 | 16 | 86 | **15** | < 0.01 s |
| n16-p40 | 224 | 169 | 2,437 | **23** | < 0.01 s |
| n16-p60 (pa zgjidhje) | 1,316 | 1,034 | 1,034 | **505** | 0.02 s |
| n24-p50 | 2,882 | 2,221 | 18,118 | **32** | 0.01 s |
| n32-p55 | 4,587 | 3,638 | timeout | **53** | 0.03 s |
| n48-p50 | 11,646 | 9,203 | timeout | **49** | 0.3 s |
| n64-p50 | 1,548 | 1,264 | timeout | **73** | 1.3 s |

### Çka tregojnë rezultatet

- **H1 → H2:** prerja e dead ends e zvogëlon numrin e nyjeve 1.2–4 herë, dhe nuk humb asnjë zgjidhje, sepse H2 është admissible.
- **H3 është më e keqja**, edhe pse përdor më shumë informacion. Termi `Σ 1/|avail(r)|` zakonisht **rritet me thellësinë**, sepse rreshtat e mbetur kanë gjithnjë e më pak opsione. Kështu nyjet e thella marrin `f` më të madh, dhe A* kthehet te nyjet e cekëta, gati si BFS. Open list rritet në qindra mijëra nyje (deri në ~600,000 te n24-p50) dhe kërkimi shpesh kalon kufirin e kohës. Mbivlerësimi i kostos e prish renditjen e A*.
- **MRV si renditje e rreshtave** ndihmon shumë: i njëjti informacion që e prish A* kur hyn në `h` (H3) është shumë i dobishëm kur përdoret për të **zgjedhur rreshtin**.
- **Mësimi:** heuristika duhet t'i prerë dead ends sa më herët (H2), por pa e mbivlerësuar koston (H3).

## 8. Heuristika admissible e propozuar: H4 (N-Rooks)

Bazuar në rezultatet e H1–H3, propozimi është:

```
h4(n) = ∞        nëse problemi i relaksuar "N-Rooks" nuk ka zgjidhje
h4(n) = N − k    përndryshe
tie(n) = Σ 1/|avail(r)|      (informacioni i H3, vetëm për barazimet)
```

**Relaksimi N-Rooks:** hiqen kufizimet e diagonaleve, dhe mbetet pyetja: *a mund të vendoset një mbretëreshë në secilin rresht të mbetur, në kolona të ndryshme, vetëm në katrorët e lirë?* Ky është problemi i **bipartite matching** (rreshta → kolona), dhe zgjidhet në kohë polinomiale me rrugë zmadhuese (augmenting paths), te `rook_matching()`.

**Pse është admissible:**
1. Nëse gjendja ka zgjidhje, në atë zgjidhje rreshtat e mbetur kanë mbretëresha në kolona të ndryshme. Pra edhe problemi i relaksuar ka zgjidhje, dhe `h4 = N − k = h*`.
2. Nëse relaksimi nuk ka zgjidhje, atëherë as problemi origjinal nuk ka, dhe `h4 = ∞ = h*`.
3. Termi `tie` nuk hyn në `f`, por vetëm rendit nyjet me të njëjtin `f` dhe `g`. Prandaj nuk e ndikon admissibility-n.

Pra `h4 ≤ h*` për çdo nyje. H4 është edhe **konsistente**: `h4(n) ≤ 1 + h4(n')`.

**Pse është më e mirë:**
- **Nga H2:** H2 sheh vetëm një rresht pa opsione. H4 sheh edhe rastet kur disa rreshta **konkurrojnë për të njëjtat kolona**. P.sh. tre rreshta kanë katrorë të lirë vetëm në dy kolona: secili rresht ka opsione, por bashkë nuk mund të plotësohen. Kjo është **kushti i Hall-it**.
- **Nga H3:** informacioni i MRV, që e prishi A* kur ishte pjesë e `h`, këtu përdoret vetëm për renditjen e barazimeve dhe nuk e mbivlerëson koston.

**Rezultati:** H4 me renditjen MRV i zgjidh të gjitha instancat në më pak se 1.5 s, me shumë më pak nyje se H2 (te instancat e mëdha **17–190 herë më pak**). Te `n16-p60` vërteton që zgjidhja nuk ekziston pas 505 nyjeve.

## 9. Ekzekutimi

Kërkohet Python 3.8+ dhe nuk ka nevojë për librari të jashtme.

```bash
cd task1

# Zgjidh shembullin e ASP Competition me H4
python blocked_queens.py

# Instancat e gatshme
python blocked_queens.py --list
python blocked_queens.py n32-p55

# Zgjidh heuristiken dhe renditjen e rreshtave
python blocked_queens.py n16-p40 -H forward --order row

# Instance nga skedari ne formatin ASP (num(i). block(i,j).)
python blocked_queens.py instanca.lp

# Krahasimi i te gjitha heuristikave ne te gjitha instancat
python compare.py
python compare.py n24-p50 n32-p55 --order mrv

# Ruaj instancat si skedare .lp
python instances.py --write instances
```

Opsionet: `-H rows|forward|mrv|rooks` (heuristika), `--order mrv|row`, `--no-board`, `--node-limit`, `--timeout`.
