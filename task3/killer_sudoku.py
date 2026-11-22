"""
Killer Sudoku - Constraint Programming (CSP).

Rregullat:
    - rrjeta 9x9 mbushet me numrat 1-9;
    - cdo rresht, kolone dhe kuti 3x3 ka numrat 1-9 pa perseritje;
    - rrjeta eshte e ndare ne "kafaze" (cages); shuma e numrave ne nje kafaz
      eshte e dhene dhe brenda kafazit numrat nuk perseriten.
    Nuk ka numra te dhene (givens): e gjithe informacioni vjen nga kafazet.

CSP (X, D, C):
    X - 81 variabla, nje per qelize
    D - domain-i i secilës {1..9}, i ruajtur si bitmask (biti v = vlera v lejohet)
    C - 27 kufizime all-different (rreshta, kolona, kuti)
        + per cdo kafaz: all-different dhe sum(qelizat) = shuma

Tri metoda zgjidhjeje (per krahasim):
    bt   - backtracking i thjeshte: qelizat me radhe, kontrollohen vetem kufizimet
    fc   - forward checking + MRV
    full - MRV + propagim i plote (constraint propagation) deri ne pike fikse:
           eliminim nga fqinjet, kombinimet e kafazeve, hidden singles
"""

import argparse
import time
from itertools import combinations

ALL = 0b1111111110                          # bitat 1..9


def popcount(x):
    return bin(x).count("1")


def digits(mask):
    return [v for v in range(1, 10) if mask >> v & 1]


ROWS = [[r * 9 + c for c in range(9)] for r in range(9)]
COLS = [[r * 9 + c for r in range(9)] for c in range(9)]
BOXES = [[(br * 3 + r) * 9 + bc * 3 + c for r in range(3) for c in range(3)]
         for br in range(3) for bc in range(3)]
UNITS = ROWS + COLS + BOXES
PEERS = [sorted({p for u in UNITS if i in u for p in u} - {i}) for i in range(81)]

# COMBOS[(k, s)] = lista e bitmask-ave te k numrave te ndryshem 1..9 me shume s
COMBOS = {}
for k in range(1, 10):
    for combo in combinations(range(1, 10), k):
        mask = sum(1 << v for v in combo)
        COMBOS.setdefault((k, sum(combo)), []).append(mask)


# ---------------------------------------------------------------------------
# Enigma
# ---------------------------------------------------------------------------

class Puzzle:
    """
    cages - lista e (shuma, [qelizat]); qelizat jane indekse 0..80 (r*9 + c).
    """

    def __init__(self, cages, name=""):
        self.cages = [(s, sorted(cells)) for s, cells in cages]
        self.name = name
        self.cage_of = [None] * 81
        for ci, (_, cells) in enumerate(self.cages):
            for i in cells:
                if self.cage_of[i] is not None:
                    raise ValueError(f"qeliza {cell_name(i)} eshte ne dy kafaze")
                self.cage_of[i] = ci
        missing = [cell_name(i) for i in range(81) if self.cage_of[i] is None]
        if missing:
            raise ValueError("qelizat pa kafaz: " + ", ".join(missing))
        # fqinjet: rresht, kolone, kuti + anetaret e kafazit (all-different)
        self.peers = [sorted(set(PEERS[i]) | set(self.cages[self.cage_of[i]][1]) - {i})
                      for i in range(81)]

    def check(self):
        """Kontrolle te thjeshta: shuma e kafazeve duhet te jete 405 (9 x 45)."""
        total = sum(s for s, _ in self.cages)
        return total == 405


def cell_name(i):
    return "ABCDEFGHI"[i // 9] + str(i % 9 + 1)


SYMBOLS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


def parse_map(text, name=""):
    """
    Formati: 9 rreshta me 9 simbole (nje per qelize, qelizat me te njejtin
    simbol jane ne te njejtin kafaz), pastaj shumat ne formen  simboli=shuma.
        aabbcdd..
        ...
        a=10 b=7 c=3 ...
    Hapesirat dhe rreshtat bosh injorohen; '#' fillon koment.
    """
    rows, sums = [], {}
    for line in text.splitlines():
        line = line.split("#")[0].strip()
        if not line:
            continue
        if "=" in line:
            for part in line.replace(",", " ").split():
                key, val = part.split("=")
                sums[key] = int(val)
        else:
            rows.append(line.replace(" ", ""))
    if len(rows) != 9 or any(len(r) != 9 for r in rows):
        raise ValueError("harta e kafazeve duhet te kete 9 rreshta me 9 simbole")
    cells = {}
    for r, row in enumerate(rows):
        for c, sym in enumerate(row):
            cells.setdefault(sym, []).append(r * 9 + c)
    missing = set(cells) - set(sums)
    if missing:
        raise ValueError("mungon shuma per kafazet: " + " ".join(sorted(missing)))
    return Puzzle([(sums[s], cells[s]) for s in cells], name)


def to_map(puzzle):
    sym = [SYMBOLS[puzzle.cage_of[i]] for i in range(81)]
    rows = ["".join(sym[r * 9:(r + 1) * 9]) for r in range(9)]
    sums = " ".join(f"{SYMBOLS[ci]}={s}" for ci, (s, _) in enumerate(puzzle.cages))
    return "\n".join(rows) + "\n" + sums + "\n"


# ---------------------------------------------------------------------------
# Kontrolli i zgjidhjes
# ---------------------------------------------------------------------------

def violations(puzzle, grid):
    """
    Objective function: numri i kufizimeve te shkelura nga rrjeta e plote.
    0 atehere dhe vetem atehere kur rrjeta eshte zgjidhje.
    """
    bad = 0
    for u in UNITS:
        bad += 9 - len({grid[i] for i in u})
    for s, cells in puzzle.cages:
        vals = [grid[i] for i in cells]
        bad += len(vals) - len(set(vals))
        bad += sum(vals) != s
    return bad


# ---------------------------------------------------------------------------
# Solver-i
# ---------------------------------------------------------------------------

class Contradiction(Exception):
    pass


class SearchLimit(Exception):
    pass


class KillerSolver:
    def __init__(self, puzzle, method="full", node_limit=None, timeout=None,
                 count_limit=1):
        self.p = puzzle
        self.method = method
        self.node_limit = node_limit
        self.timeout = timeout
        self.count_limit = count_limit      # 2 per te kontrolluar unicitetin
        self.solutions = []
        self.stats = {"nodes": 0, "backtracks": 0, "time": 0.0, "status": ""}

    # -- ndihmese ---------------------------------------------------------------

    def _tick(self):
        self.stats["nodes"] += 1
        if self.node_limit is not None and self.stats["nodes"] > self.node_limit:
            raise SearchLimit("kufiri i nyjeve")
        if self.timeout is not None and (self.stats["nodes"] & 0x3FF) == 0 \
                and time.perf_counter() - self.t0 > self.timeout:
            raise SearchLimit("timeout")

    def solve(self):
        self.t0 = time.perf_counter()
        try:
            if self.method == "bt":
                self._bt(0, [0] * 81)
            else:
                dom = [ALL] * 81
                if self.method == "full":
                    dom = self._propagate(dom)
                else:
                    dom = self._cage_bounds_initial(dom)
                self._search(dom, [False] * 81)
            self.stats["status"] = "zgjidhje" if self.solutions else "nuk ka zgjidhje"
        except (SearchLimit, Contradiction) as e:
            if isinstance(e, Contradiction):
                self.stats["status"] = "nuk ka zgjidhje"
            else:
                self.stats["status"] = str(e)
        self.stats["time"] = time.perf_counter() - self.t0
        return self.solutions[0] if self.solutions else None

    # -- (1) backtracking i thjeshte ---------------------------------------------

    def _consistent(self, grid, i, v):
        for p in PEERS[i]:
            if grid[p] == v:
                return False
        s, cells = self.p.cages[self.p.cage_of[i]]
        total, filled = v, 1
        for j in cells:
            if j != i and grid[j]:
                if grid[j] == v:
                    return False
                total += grid[j]
                filled += 1
        if filled == len(cells):
            return total == s
        return total < s

    def _bt(self, i, grid):
        if i == 81:
            self.solutions.append(grid[:])
            return len(self.solutions) >= self.count_limit
        self._tick()
        for v in range(1, 10):
            if self._consistent(grid, i, v):
                grid[i] = v
                if self._bt(i + 1, grid):
                    return True
                grid[i] = 0
        self.stats["backtracks"] += 1
        return False

    # -- kufijte e kafazeve (perdoren nga fc dhe full) ----------------------------

    def _cage_filter(self, dom, ci):
        """
        Per kafazin ci: mbahen vetem kombinimet e numrave qe (1) kane shumen e
        duhur, (2) nuk perdorin numra te zene ne kafaz, (3) mund te vendosen ne
        domain-et e qelizave te mbetura. Domain-et kufizohen ne bashkimin e
        kombinimeve te mbetura. Kthen listen e qelizave te ndryshuara.
        """
        s, cells = self.p.cages[ci]
        used, total, rest = 0, 0, []
        for i in cells:
            d = dom[i]
            if popcount(d) == 1:
                v = d.bit_length() - 1
                if used >> v & 1:
                    raise Contradiction
                used |= d
                total += v
            else:
                rest.append(i)
        if not rest:
            if total != s:
                raise Contradiction
            return []
        union_dom = 0
        for i in rest:
            union_dom |= dom[i]
        allowed = 0
        for combo in COMBOS.get((len(rest), s - total), ()):
            if combo & used or combo & ~union_dom:
                continue
            if all(dom[i] & combo for i in rest):
                allowed |= combo
        if not allowed:
            raise Contradiction
        changed = []
        for i in rest:
            nd = dom[i] & allowed
            if nd != dom[i]:
                if not nd:
                    raise Contradiction
                dom[i] = nd
                changed.append(i)
        return changed

    def _cage_bounds_initial(self, dom):
        dom = dom[:]
        for ci in range(len(self.p.cages)):
            self._cage_filter(dom, ci)
        return dom

    # -- (2) forward checking dhe (3) propagimi i plote --------------------------

    def _assign_fc(self, dom, i, v):
        """Forward checking: v largohet nga domain-et e fqinjeve te qelizes i."""
        dom = dom[:]
        dom[i] = 1 << v
        bit = 1 << v
        for p in self.p.peers[i]:
            if dom[p] & bit:
                dom[p] &= ~bit
                if not dom[p]:
                    raise Contradiction
        self._cage_filter(dom, self.p.cage_of[i])
        return dom

    def _propagate(self, dom):
        """
        Propagim deri ne pike fikse (asnje domain nuk ndryshon me):
          1. qelize me nje vlere -> vlera largohet nga fqinjet (naked single)
          2. kombinimet e kafazeve (_cage_filter)
          3. hidden single: nese nje numer mund te shkoje vetem ne nje qelize te
             njesise, ajo qelize e merr ate numer
        """
        dom = dom[:]
        done = [False] * 81
        changed = True
        while changed:
            changed = False
            for i in range(81):
                d = dom[i]
                if not done[i] and popcount(d) == 1:
                    done[i] = True
                    for p in self.p.peers[i]:
                        if dom[p] & d:
                            dom[p] &= ~d
                            if not dom[p]:
                                raise Contradiction
                            changed = True
            for ci in range(len(self.p.cages)):
                if self._cage_filter(dom, ci):
                    changed = True
            for u in UNITS:
                for v in range(1, 10):
                    bit = 1 << v
                    where = [i for i in u if dom[i] & bit]
                    if not where:
                        raise Contradiction
                    if len(where) == 1 and dom[where[0]] != bit:
                        dom[where[0]] = bit
                        changed = True
        return dom

    def _search(self, dom, assigned):
        """
        assigned[i] = True kur qelizes i i eshte dhene vlere nga kerkimi (fc).
        Te "full", qeliza me nje vlere te vetme eshte e caktuar, sepse propagimi
        e ka larguar tashme ate vlere nga fqinjet.
        """
        self._tick()
        full = self.method == "full"
        # MRV: qeliza e pacaktuar me domain-in me te vogel
        best, best_cnt = None, 10
        for i in range(81):
            cnt = popcount(dom[i])
            if (cnt > 1 if full else not assigned[i]) and cnt < best_cnt:
                best, best_cnt = i, cnt
                if cnt <= 2:
                    break
        if best is None:                                # te gjitha qelizat kane 1 vlere
            grid = [d.bit_length() - 1 for d in dom]
            if violations(self.p, grid) == 0:
                self.solutions.append(grid)
            return len(self.solutions) >= self.count_limit
        for v in digits(dom[best]):
            try:
                if self.method == "full":
                    child = dom[:]
                    child[best] = 1 << v
                    child = self._propagate(child)
                    child_assigned = assigned
                else:
                    child = self._assign_fc(dom, best, v)
                    child_assigned = assigned[:]
                    child_assigned[best] = True
            except Contradiction:
                continue                                # dega pritet
            if self._search(child, child_assigned):
                return True
        self.stats["backtracks"] += 1
        return False


def solve(puzzle, method="full", node_limit=None, timeout=None, count_limit=1):
    s = KillerSolver(puzzle, method, node_limit, timeout, count_limit)
    grid = s.solve()
    return grid, s.stats, s.solutions


# ---------------------------------------------------------------------------
# Shfaqja
# ---------------------------------------------------------------------------

def format_cages(puzzle):
    """Harta e kafazeve: cdo kafaz shfaqet me nje simbol, plus shumat."""
    lines = []
    for r in range(9):
        if r and r % 3 == 0:
            lines.append("------+-------+------")
        row = ""
        for c in range(9):
            if c and c % 3 == 0:
                row += "| "
            row += SYMBOLS[puzzle.cage_of[r * 9 + c]] + " "
        lines.append(row.rstrip())
    sums = [f"{SYMBOLS[ci]}={s}" for ci, (s, _) in enumerate(puzzle.cages)]
    for k in range(0, len(sums), 12):
        lines.append(" ".join(sums[k:k + 12]))
    return "\n".join(lines)


def format_grid(grid):
    lines = []
    for r in range(9):
        if r and r % 3 == 0:
            lines.append("------+-------+------")
        row = ""
        for c in range(9):
            if c and c % 3 == 0:
                row += "| "
            row += str(grid[r * 9 + c]) + " "
        lines.append(row.rstrip())
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

METHODS = {"bt": "Backtracking i thjeshte",
           "fc": "Forward checking + MRV",
           "full": "MRV + propagim i plote"}


def main():
    from puzzles import PUZZLES, load

    ap = argparse.ArgumentParser(description="Killer Sudoku me Constraint Programming")
    ap.add_argument("puzzle", nargs="?", default="easy-1",
                    help="emri i enigmes (shih --list) ose rruga e nje skedari")
    ap.add_argument("-m", "--method", default="full", choices=METHODS,
                    help="metoda: bt, fc ose full (default)")
    ap.add_argument("--list", action="store_true", help="shfaq enigmat")
    ap.add_argument("--unique", action="store_true",
                    help="kontrollo nese zgjidhja eshte unike")
    ap.add_argument("--node-limit", type=int, default=5_000_000)
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args()

    if args.list:
        for name in PUZZLES:
            p = load(name)
            sizes = [len(c) for _, c in p.cages]
            print(f"{name:<10} kafaze={len(p.cages):<3} madhesia {min(sizes)}-{max(sizes)}")
        return

    puzzle = load(args.puzzle)
    print(f"Enigma: {puzzle.name}  |  {len(puzzle.cages)} kafaze  |  "
          f"metoda: {METHODS[args.method]}\n")
    print(format_cages(puzzle) + "\n")
    if not puzzle.check():
        print("Kujdes: shuma e kafazeve nuk eshte 405, enigma nuk ka zgjidhje.\n")

    grid, s, sols = solve(puzzle, args.method, args.node_limit, args.timeout,
                          count_limit=2 if args.unique else 1)
    print(f"Statusi: {s['status']}")
    if grid is not None:
        print("\n" + format_grid(grid) + "\n")
        print(f"Kufizime te shkelura = {violations(puzzle, grid)} | "
              f"valid = {violations(puzzle, grid) == 0}")
    if args.unique and s["status"] in ("zgjidhje", "nuk ka zgjidhje"):
        print(f"Zgjidhja eshte unike: {len(sols) == 1}")
    print(f"Nyje: {s['nodes']:,} | backtracks: {s['backtracks']:,} | koha: {s['time']:.3f}s")


if __name__ == "__main__":
    main()
