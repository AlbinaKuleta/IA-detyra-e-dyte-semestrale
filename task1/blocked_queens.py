"""
Blocked N-Queens - A* (A Star) me heuristika.

Problemi: ne nje tabele N x N duhet te vendosen N mbretresha ne katroret
jo te bllokuar, ashtu qe asnje cift mbretreshash te mos jete ne te njejtin
rresht, kolone ose diagonale.

Formati i hyrjes (si ne ASP Competition):
    num(1). num(2). ... num(N).  block(i,j). ...
Formati i daljes:
    queen(i,j). ...      (i = rreshti, j = kolona, duke filluar nga 1)

Modelimi per A*:
    - Gjendja: bashkesia e mbretreshave te vendosura (te shumten nje per rresht)
      dhe, per cdo rresht te mbetur, kolonat ende te lira.
    - Veprimi: vendos nje mbretreshe ne nje katror te lire te nje rreshti te
      mbetur. Rreshti zgjidhet me MRV (ai me me pak katrore te lire) ose me
      radhe 1, 2, ..., N (opsioni --order row).
    - Kostoja e hapit: 1, prandaj g(n) = k (numri i mbretreshave te vendosura).
    - Qellimi: k = N. Cdo zgjidhje ka kosto N.
    - f(n) = g(n) + h(n). Nyjet me f te barabarte renditen sipas g me te madh
      (me thelle), pastaj sipas celesit dytesor `tie` te heuristikes.
"""

import argparse
import heapq
import re
import time

INF = float("inf")


# ---------------------------------------------------------------------------
# Instanca
# ---------------------------------------------------------------------------

class Instance:
    """Tabela N x N me katroret e bllokuar (indekset brenda jane nga 0)."""

    def __init__(self, n, blocked, name=""):
        self.n = n
        self.name = name
        self.blocked = sorted(set(blocked))
        self.full = (1 << n) - 1
        self.blocked_mask = [0] * n          # bitat e kolonave te bllokuara per rresht
        for r, c in self.blocked:
            self.blocked_mask[r] |= 1 << c

    def to_asp(self):
        nums = " ".join(f"num({i})." for i in range(1, self.n + 1))
        blocks = " ".join(f"block({r + 1},{c + 1})." for r, c in self.blocked)
        return nums + "\n" + blocks + "\n"


def parse_asp(text, name=""):
    """Lexon formatin num(i). block(i,j). dhe kthen nje Instance."""
    nums = [int(x) for x in re.findall(r"num\(\s*(\d+)\s*\)", text)]
    blocks = [(int(a) - 1, int(b) - 1)
              for a, b in re.findall(r"block\(\s*(\d+)\s*,\s*(\d+)\s*\)", text)]
    if not nums:
        raise ValueError("hyrja nuk ka asnje num(i).")
    return Instance(max(nums), blocks, name)


# ---------------------------------------------------------------------------
# Gjendja
# ---------------------------------------------------------------------------
#
# Nje gjendje ruhet si tuple:
#     (queens, avail)
#   queens - tuple me ciftet (rreshti, kolona) te mbretreshave te vendosura
#   avail  - tuple me ciftet (rreshti, bitmask) per rreshtat e mbetur; bitmask-u
#            mban kolonat ende te lira (jo te bllokuara dhe jo te sulmuara)
#
# Kur vendoset mbretresha ne (r0, c), per cdo rresht tjeter r me d = |r - r0|
# largohen kolonat c, c - d dhe c + d (kolona dhe dy diagonalet).


def initial_state(inst):
    avail = tuple((r, inst.full & ~inst.blocked_mask[r]) for r in range(inst.n))
    return (), avail


def popcount(x):
    return bin(x).count("1")


def successors(inst, state, order="mrv"):
    queens, avail = state
    if order == "mrv":
        i = min(range(len(avail)), key=lambda j: popcount(avail[j][1]))
    else:
        i = 0
    row, mask = avail[i]
    rest = avail[:i] + avail[i + 1:]
    full = inst.full
    while mask:
        bit = mask & -mask
        mask ^= bit
        c = bit.bit_length() - 1
        new = tuple((r, m & ~(bit | (bit << abs(r - row)) | (bit >> abs(r - row))) & full)
                    for r, m in rest)
        yield (row, c), (queens + ((row, c),), new)


# ---------------------------------------------------------------------------
# Heuristikat
# ---------------------------------------------------------------------------
#
# Secila kthen (h, tie): h hyn ne f = g + h, ndersa `tie` perdoret vetem per
# te renditur nyjet me f dhe g te barabarte (sa me i vogel, aq me mire).
# h = INF do te thote "dead end": nyja nuk futet ne open list.
#
# Kostoja e vertete e mbetur per nje gjendje te zgjidhshme eshte h* = N - k
# (duhen edhe N - k mbretresha), ndersa per nje gjendje pa zgjidhje h* = INF.
# Nje heuristike eshte admissible kur h <= h* per cdo gjendje.


def h_rows(inst, state):
    """
    H1 - rreshtat e mbetur:  h = N - k.
    Admissible (h = h* per gjendjet e zgjidhshme), por nuk i dallon dead ends.
    """
    return len(state[1]), 0


def h_forward(inst, state):
    """
    H2 - forward checking:
        h = INF    nese ndonje rresht i mbetur nuk ka asnje katror te lire
        h = N - k  perndryshe
    Admissible: INF jepet vetem kur eshte e sigurt qe nuk ka zgjidhje.
    """
    for _, mask in state[1]:
        if mask == 0:
            return INF, 0
    return len(state[1]), 0


def h_mrv(inst, state):
    """
    H3 - MRV (Minimum Remaining Values):
        h = (N - k) + sum_{r te mbetur} 1 / |avail(r)|      (INF nese ndonje = 0)
    Rreshtat me pak opsione e rrisin h. Jo admissible: per cdo gjendje te
    zgjidhshme me k < N, h > N - k = h*.
    """
    total = 0.0
    for _, mask in state[1]:
        cnt = popcount(mask)
        if cnt == 0:
            return INF, 0
        total += 1.0 / cnt
    return len(state[1]) + total, 0


def rook_matching(masks):
    """
    Relaksimi N-Rooks: hiqen kufizimet e diagonaleve dhe pyetet a mund te
    vendoset nga nje mbretreshe ne secilin rresht te mbetur ne kolona te
    ndryshme. Kjo eshte perputhje (bipartite matching) rreshta -> kolona,
    e zgjidhur me rruge zmadhuese (augmenting paths).
    Kthen True nese ekziston perputhje e plote.
    """
    match_col = {}                      # kolona (bit) -> indeksi i rreshtit

    def try_row(i, seen):
        mask = masks[i]
        while mask:
            bit = mask & -mask
            mask ^= bit
            if bit in seen:
                continue
            seen.add(bit)
            if bit not in match_col or try_row(match_col[bit], seen):
                match_col[bit] = i
                return True
        return False

    for i in sorted(range(len(masks)), key=lambda j: popcount(masks[j])):
        if not try_row(i, set()):
            return False
    return True


def h_rooks(inst, state):
    """
    H4 - heuristika admissible e propozuar (bazuar ne rezultatet e H1-H3):
        h = INF     nese relaksimi N-Rooks nuk ka zgjidhje
        h = N - k   perndryshe
        tie = sum_{r te mbetur} 1 / |avail(r)|     (informacioni i H3)
    Ne cdo zgjidhje te vertete, rreshtat e mbetur kane mbretresha ne kolona te
    ndryshme, pra edhe problemi i relaksuar ka zgjidhje. Prandaj INF jepet
    vetem kur nuk ka zgjidhje dhe h <= h* (admissible). Termi i MRV hyn vetem
    ne `tie`, jo ne f, prandaj nuk e prish admissibility-n.
    """
    masks = [m for _, m in state[1]]
    tie = 0.0
    for m in masks:
        cnt = popcount(m)
        if cnt == 0:
            return INF, 0
        tie += 1.0 / cnt
    if not rook_matching(masks):
        return INF, 0
    return len(masks), tie


HEURISTICS = {
    "rows": ("H1 rreshtat e mbetur", h_rows, True),
    "forward": ("H2 forward checking", h_forward, True),
    "mrv": ("H3 MRV", h_mrv, False),
    "rooks": ("H4 N-Rooks (propozimi)", h_rooks, True),
}


# ---------------------------------------------------------------------------
# A*
# ---------------------------------------------------------------------------

def astar(inst, heuristic, order="mrv", node_limit=None, timeout=None):
    """
    A* me priority queue (heapq). Celesi: (f, -g, tie, numeruesi).
    Pema e kerkimit nuk ka gjendje te perseritura (rreshti qe mbushet ne
    secilen gjendje eshte i percaktuar), prandaj nuk nevojitet closed list.
    Kthen (zgjidhja ose None, statistikat).
    """
    t0 = time.perf_counter()
    stats = {"expanded": 0, "generated": 1, "pruned": 0, "max_open": 1,
             "time": 0.0, "status": ""}

    start = initial_state(inst)
    h, tie = heuristic(inst, start)
    counter = 0
    open_list = []
    if h < INF:
        heapq.heappush(open_list, (h, 0, tie, counter, start))
    else:
        stats["pruned"] += 1

    solution = None
    while open_list:
        f, neg_g, _, _, state = heapq.heappop(open_list)
        queens, avail = state
        if not avail:                               # k = N -> qellimi
            solution = tuple(c for _, c in sorted(queens))
            break

        stats["expanded"] += 1
        if node_limit is not None and stats["expanded"] > node_limit:
            stats["status"] = "kufiri i nyjeve"
            break
        if timeout is not None and (stats["expanded"] & 0xFF) == 0 \
                and time.perf_counter() - t0 > timeout:
            stats["status"] = "timeout"
            break

        g = -neg_g + 1
        for _, child in successors(inst, state, order):
            stats["generated"] += 1
            h, tie = heuristic(inst, child)
            if h == INF:                            # dead end -> dega pritet
                stats["pruned"] += 1
                continue
            counter += 1
            heapq.heappush(open_list, (g + h, -g, tie, counter, child))
        stats["max_open"] = max(stats["max_open"], len(open_list))

    if not stats["status"]:
        stats["status"] = "zgjidhje" if solution is not None else "nuk ka zgjidhje"
    stats["time"] = time.perf_counter() - t0
    return solution, stats


# ---------------------------------------------------------------------------
# Verifikimi dhe shfaqja
# ---------------------------------------------------------------------------

def conflicts(inst, queens):
    """
    Objective function: numri i cifteve te mbretreshave qe sulmojne njera-tjetren
    plus mbretreshat ne katrore te bllokuar. queens[r] = kolona ne rreshtin r.
    conflicts = 0 atehere dhe vetem atehere kur zgjidhja eshte valide.
    """
    bad = sum(1 for r, c in enumerate(queens) if inst.blocked_mask[r] >> c & 1)
    for r1 in range(len(queens)):
        for r2 in range(r1 + 1, len(queens)):
            c1, c2 = queens[r1], queens[r2]
            if c1 == c2 or abs(c1 - c2) == r2 - r1:
                bad += 1
    return bad


def is_valid(inst, queens):
    return queens is not None and len(queens) == inst.n and conflicts(inst, queens) == 0


def format_board(inst, queens=None):
    lines = []
    for r in range(inst.n):
        row = []
        for c in range(inst.n):
            if queens is not None and queens[r] == c:
                row.append("Q")
            elif inst.blocked_mask[r] >> c & 1:
                row.append("#")
            else:
                row.append(".")
        lines.append(" ".join(row))
    return "\n".join(lines)


def format_asp(queens):
    return " ".join(f"queen({r + 1},{c + 1})." for r, c in enumerate(queens))


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    from instances import INSTANCES, load

    ap = argparse.ArgumentParser(description="Blocked N-Queens me A*")
    ap.add_argument("instance", nargs="?", default="example",
                    help="emri i instances (shih --list) ose rruga e nje skedari .lp")
    ap.add_argument("-H", "--heuristic", default="rooks", choices=HEURISTICS,
                    help="heuristika (default: rooks)")
    ap.add_argument("--order", default="mrv", choices=["mrv", "row"],
                    help="cili rresht mbushet: mrv (default) ose row (me radhe)")
    ap.add_argument("--list", action="store_true", help="shfaq instancat")
    ap.add_argument("--no-board", action="store_true", help="mos e vizato tabelen")
    ap.add_argument("--node-limit", type=int, default=2_000_000)
    ap.add_argument("--timeout", type=float, default=120.0)
    args = ap.parse_args()

    if args.list:
        for name in INSTANCES:
            inst = load(name)
            print(f"{name:<10} N={inst.n:<3} te bllokuar={len(inst.blocked)}")
        return

    inst = load(args.instance)
    label, heuristic, admissible = HEURISTICS[args.heuristic]
    print(f"Instanca: {inst.name}  N={inst.n}  te bllokuar={len(inst.blocked)}")
    print(f"Heuristika: {label} ({'admissible' if admissible else 'jo admissible'}), "
          f"renditja e rreshtave: {args.order}\n")
    if not args.no_board:
        print(format_board(inst) + "\n")

    solution, s = astar(inst, heuristic, args.order, args.node_limit, args.timeout)
    print(f"Statusi: {s['status']}")
    if solution is not None:
        if not args.no_board:
            print("\n" + format_board(inst, solution) + "\n")
        print(format_asp(solution))
        print(f"\nKonflikte = {conflicts(inst, solution)} | valid = {is_valid(inst, solution)}")
    print(f"Nyje te zgjeruara: {s['expanded']:,} | te gjeneruara: {s['generated']:,} | "
          f"te prera (h = INF): {s['pruned']:,} | open maksimal: {s['max_open']:,} | "
          f"koha: {s['time']:.3f}s")


if __name__ == "__main__":
    main()
