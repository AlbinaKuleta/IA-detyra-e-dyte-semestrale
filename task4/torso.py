"""
Torso Decompositions (ESA SpOC-3, Challenge 1) - modeli dhe vleresimi.

Hyrja: graf i padrejtuar G me nyjet 0..n-1 (skedar .gr, nje brinje "u v" per rresht).

Vektori i vendimit:  x = [p_1, ..., p_n, t]
    p   - permutacion i nyjeve
    t   - pragu: torso jane n - t nyjet e fundit te permutacionit

Vleresimi:
    1. Permutacioni i orienton brinjet: {u, v} -> (u, v) nese u eshte para v.
    2. Fill-in: permutacioni lexohet nga e majta ne te djathte; kur nje nyje u ka
       dy brinje dalese drejt v dhe w qe nuk jane te lidhura, shtohet brinja {v, w}
       (e orientuar sipas permutacionit).
    3. outdeg(u) = numri i brinjeve dalese te u ne grafin e mbushur.
    4. Torso size  = n - t                                   (maksimizohet)
       Torso width = max outdeg(u) per u ne torso            (minimizohet)

Problemi eshte me dy objektiva. Rezultati eshte nje bashkesi (deri ne 20)
vektoresh qe perafrojne frontin Pareto, e vleresuar me hypervolume.
"""

import os

WIDTH_CAP = 501          # sipas rregullave: gjeresia mbi 500 vleresohet si 501


# ---------------------------------------------------------------------------
# Grafi
# ---------------------------------------------------------------------------

class Graph:
    def __init__(self, n, edges, name=""):
        self.n = n
        self.name = name
        self.edges = [(u, v) for u, v in edges if u != v]
        self.adj = [[] for _ in range(n)]
        for u, v in self.edges:
            self.adj[u].append(v)
            self.adj[v].append(u)

    @property
    def m(self):
        return len(self.edges)


def load_graph(path):
    edges = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 2 and not line.startswith(("#", "c", "p")):
                edges.append((int(parts[0]), int(parts[1])))
    n = max(max(e) for e in edges) + 1
    return Graph(n, edges, os.path.splitext(os.path.basename(path))[0])


# Shembulli nga pershkrimi i detyres: x = [0,1,2,4,5,3,6,8,9,7, 6] -> size 4, width 2
EXAMPLE_EDGES = [(0, 1), (0, 2), (1, 6), (2, 8), (3, 8), (3, 9), (4, 5), (4, 6), (4, 7)]
EXAMPLE_X = [0, 1, 2, 4, 5, 3, 6, 8, 9, 7, 6]


def example_graph():
    return Graph(10, EXAMPLE_EDGES, "shembull")


# ---------------------------------------------------------------------------
# Vleresimi
# ---------------------------------------------------------------------------

def out_degrees(graph, perm):
    """
    Kthen outdeg[i] = shkalla dalese e nyjes ne poziten i te permutacionit,
    pas fill-in-it.

    Bashkesite e fqinjeve te mevonshem ruhen si bitmask mbi pozitat (int i
    Python-it). Kur procesohet pozita i me fqinjet e mevonshem S, mjafton qe
    S - {j} t'i shtohet nyjes j = pozita me e hershme ne S: kur te procesohet
    j, ato do te behen fqinjet e tij dhe fill-in-i vazhdon me tej. Kjo jep te
    njejtin graf te mbushur si shtimi i te gjitha brinjeve {v, w} (Tarjan &
    Yannakakis), por me n veprime ne vend te deg^2.
    """
    n = graph.n
    pos = [0] * n
    for i, v in enumerate(perm):
        pos[v] = i
    out = [0] * n
    for u, v in graph.edges:
        a, b = pos[u], pos[v]
        if a < b:
            out[a] |= 1 << b
        else:
            out[b] |= 1 << a
    deg = [0] * n
    for i in range(n):
        s = out[i]
        if s:
            deg[i] = s.bit_count()
            low = s & -s                       # pozita me e hershme ne S
            j = low.bit_length() - 1
            out[j] |= s ^ low
    return deg


def width_profile(deg):
    """
    w[t] = gjeresia e torsos qe fillon ne poziten t = max(deg[t:]).
    Nje permutacion jep njekohesisht zgjidhje per te gjitha t.
    """
    n = len(deg)
    w = [0] * n
    cur = 0
    for t in range(n - 1, -1, -1):
        cur = max(cur, deg[t])
        w[t] = cur
    return w


def evaluate(graph, x):
    """Vektori x = [perm..., t] -> (torso size, torso width)."""
    perm, t = list(x[:-1]), int(x[-1])
    check_vector(graph, x)
    deg = out_degrees(graph, perm)
    width = max(deg[t:]) if t < graph.n else 0
    return graph.n - t, min(width, WIDTH_CAP)   # gjeresia mbi 500 numerohet si 501


def check_vector(graph, x):
    n = graph.n
    if len(x) != n + 1:
        raise ValueError(f"vektori duhet te kete {n + 1} elemente")
    if sorted(x[:-1]) != list(range(n)):
        raise ValueError("p_1..p_n nuk eshte permutacion i 0..n-1")
    if not 0 <= x[-1] <= n - 1:
        raise ValueError("t duhet te jete ne 0..n-1")


def front_points(w):
    """
    Pikat jo te dominuara (t, width) te nje profili: per cdo gjeresi,
    t me e vogel (torso me e madhe).
    """
    pts = []
    for t in range(len(w)):
        if t == 0 or w[t] < w[t - 1]:
            pts.append((t, w[t]))
    return pts


def hypervolume(points, n, ref_width=WIDTH_CAP):
    """
    Hypervolume 2D per objektivat (t, width), te dyja minimizohen, me pike
    reference (n, ref_width). Sa me i madh, aq me mire.
    points - lista e (t, width); pikat e dominuara nuk ndikojne.
    """
    best = {}
    for t, wd in points:
        if wd < ref_width and t < n:
            best[t] = min(best.get(t, ref_width), wd)
    hv, cur_w = 0, ref_width
    ts = sorted(best)
    for k, t in enumerate(ts):
        cur_w = min(cur_w, best[t])
        nxt = ts[k + 1] if k + 1 < len(ts) else n
        hv += (nxt - t) * (ref_width - cur_w)
    return hv


def profile_hv(w, ref_width=WIDTH_CAP):
    """Hypervolume i te gjitha pikave te nje profili = sum_t (ref - w[t])."""
    return sum(ref_width - min(x, ref_width) for x in w)


# ---------------------------------------------------------------------------
# Arkivi Pareto
# ---------------------------------------------------------------------------

class Archive:
    """
    Ruan per cdo gjeresi w pragun me te vogel t te gjetur deri tani dhe
    permutacionin perkates. Prej tyre zgjidhen deri ne 20 vektore.
    """

    def __init__(self, graph):
        self.graph = graph
        self.best = {}                         # width -> (t, perm)

    def add(self, perm, w):
        changed = False
        for t, wd in front_points(w):
            if wd >= WIDTH_CAP:
                continue
            if wd not in self.best or t < self.best[wd][0]:
                self.best[wd] = (t, tuple(perm))
                changed = True
        return changed

    def points(self):
        """Pikat jo te dominuara (t, width, perm), te renditura sipas t."""
        pts, min_t = [], None
        for wd in sorted(self.best):
            t, perm = self.best[wd]
            if min_t is None or t < min_t:
                pts.append((t, wd, perm))
                min_t = t
        return sorted(pts)

    def hv(self):
        return hypervolume([(t, wd) for t, wd, _ in self.points()], self.graph.n)

    def select(self, k=20):
        """
        Zgjedh k pika me hypervolume sa me te madh (greedy: ne cdo hap shtohet
        pika qe e rrit HV me se shumti).
        """
        pts = self.points()
        chosen = []
        n = self.graph.n
        while pts and len(chosen) < k:
            base = hypervolume([(t, wd) for t, wd, _ in chosen], n)
            best = max(pts, key=lambda p: hypervolume(
                [(t, wd) for t, wd, _ in chosen] + [(p[0], p[1])], n) - base)
            chosen.append(best)
            pts.remove(best)
        return sorted(chosen)

    def vectors(self, k=20):
        return [list(perm) + [t] for t, wd, perm in self.select(k)]
