"""
Metaheuristikat per Torso Decompositions.

Ideja (metoda epsilon-constraint): fronti Pareto ndertohet duke zgjidhur nje
problem me nje objektiv per secilen gjeresi maksimale k:

    maksimizo  size_k(p) = madhesia e torsos me te madhe me gjeresi <= k

Te nje permutacion p, size_k(p) = n - (pozita e fundit me outdeg > k) - 1:
te gjitha nyjet pas nyjes se fundit "shkelese" formojne torso.

Funksioni objektiv per kerkimin:
    f_k(p) = size_k(p) - 0.01 * sum_{i: outdeg(i) > k} (outdeg(i) - k)
Termi i dyte (teprica e gjeresise) e udhezon kerkimin edhe kur size_k nuk
ndryshon: sa me pak teprice, aq me afer jemi nje torso me te madhe.

Levizja (fqinjesia): nje nyje me outdeg > k (zakonisht nje nga te fundit)
zhvendoset ne nje pozite tjeter te permutacionit (insertion move).

Cdo permutacion i vleresuar jep pika per te gjitha k njekohesisht, prandaj
te gjitha shtohen ne nje arkiv te perbashket Pareto.
"""

import math
import random
import time

from torso import Archive, out_degrees, width_profile


# ---------------------------------------------------------------------------
# Heuristikat konstruktive (baseline)
# ---------------------------------------------------------------------------

def random_order(graph, rng):
    p = list(range(graph.n))
    rng.shuffle(p)
    return p


def min_degree_order(graph):
    """
    Heuristika klasike "minimum degree" per elimination orderings: ne cdo hap
    eliminohet nyja me shkallen me te vogel ne grafin e mbetur, dhe fqinjet e
    saj lidhen mes vete (fill-in). Jep gjeresi te vogel per te gjithe grafin.
    """
    n = graph.n
    adj = [0] * n
    for u, v in graph.edges:
        adj[u] |= 1 << v
        adj[v] |= 1 << u
    alive = (1 << n) - 1
    deg = [a.bit_count() for a in adj]
    remaining = set(range(n))
    order = []
    for _ in range(n):
        best = min(remaining, key=lambda v: (deg[v], v))
        remaining.remove(best)
        nb = adj[best] & alive
        alive &= ~(1 << best)
        order.append(best)
        m = nb
        while m:
            low = m & -m
            u = low.bit_length() - 1
            m ^= low
            adj[u] = (adj[u] | nb) & ~low & alive
            deg[u] = adj[u].bit_count()
    return order


# ---------------------------------------------------------------------------
# Objektivi epsilon-constraint
# ---------------------------------------------------------------------------

def score(deg, k):
    """Kthen (f_k, size_k, lista e pozitave shkelese)."""
    n = len(deg)
    viol = [i for i in range(n) if deg[i] > k]
    size = n - (viol[-1] + 1) if viol else n
    excess = sum(deg[i] - k for i in viol)
    return size - 0.01 * excess, size, viol


def neighbor(perm, viol, rng):
    """
    Insertion move: zgjidhet nje nyje shkelese (70%: nje nga 5 te fundit, qe
    e kufizojne torson; 30%: cilado) dhe zhvendoset ne nje pozite te
    rastesishme (50%: me heret, 50%: kudo).
    """
    n = len(perm)
    i = rng.choice(viol[-5:]) if rng.random() < 0.7 else rng.choice(viol)
    j = rng.randrange(0, i + 1) if rng.random() < 0.5 else rng.randrange(n)
    q = perm[:]
    q.insert(j, q.pop(i))
    return q


# ---------------------------------------------------------------------------
# Simulated Annealing
# ---------------------------------------------------------------------------

def simulated_annealing(graph, k, start, seconds, archive, rng, t_start=5.0, t_end=0.05):
    """
    SA per gjeresine k. Temperatura bie ne menyre gjeometrike nga t_start ne
    t_end gjate kohes se dhene. Zgjidhja me e keqe pranohet me probabilitet
    exp(delta / T) (kriteri i Metropolis).
    """
    p = start[:]
    deg = out_degrees(graph, p)
    archive.add(p, width_profile(deg))
    cur, size, viol = score(deg, k)
    best_size, best_p = size, p
    t0 = time.perf_counter()
    iters = accepted = 0
    while viol:
        elapsed = time.perf_counter() - t0
        if elapsed >= seconds:
            break
        T = t_start * (t_end / t_start) ** (elapsed / seconds)
        q = neighbor(p, viol, rng)
        dq = out_degrees(graph, q)
        val, s, vq = score(dq, k)
        iters += 1
        if val >= cur or rng.random() < math.exp((val - cur) / T):
            p, cur, viol = q, val, vq
            accepted += 1
            archive.add(q, width_profile(dq))
            if s > best_size:
                best_size, best_p = s, q
    return best_p, best_size, iters, accepted


# ---------------------------------------------------------------------------
# Iterated Local Search
# ---------------------------------------------------------------------------

def iterated_local_search(graph, k, start, seconds, archive, rng, patience=60, kick=8):
    """
    ILS per gjeresine k: hill climbing (pranohen vetem levizjet qe nuk e
    perkeqesojne f_k); kur nuk ka permiresim per `patience` hapa, zgjidhja me
    e mire "shqetesohet" (perturbation) me `kick` levizje te rastesishme dhe
    kerkimi vazhdon prej saj.
    """
    p = start[:]
    deg = out_degrees(graph, p)
    archive.add(p, width_profile(deg))
    cur, size, viol = score(deg, k)
    best_val, best_size, best_p = cur, size, p
    t0 = time.perf_counter()
    iters = accepted = stale = 0
    while viol and time.perf_counter() - t0 < seconds:
        q = neighbor(p, viol, rng)
        dq = out_degrees(graph, q)
        val, s, vq = score(dq, k)
        iters += 1
        if val >= cur:
            if val > cur:
                stale = 0
            p, cur, viol = q, val, vq
            accepted += 1
            archive.add(q, width_profile(dq))
            if val > best_val:
                best_val, best_size, best_p = val, s, q
        stale += 1
        if stale >= patience:                      # perturbation nga me e mira
            p = best_p[:]
            for _ in range(kick):
                i, j = rng.randrange(graph.n), rng.randrange(graph.n)
                p.insert(j, p.pop(i))
            deg = out_degrees(graph, p)
            cur, _, viol = score(deg, k)
            stale = 0
    return best_p, best_size, iters, accepted


METHODS = {"sa": ("Simulated Annealing", simulated_annealing),
           "ils": ("Iterated Local Search", iterated_local_search)}


# ---------------------------------------------------------------------------
# Optimizimi me shume objektiva (epsilon-constraint)
# ---------------------------------------------------------------------------

def width_targets(w0, count=12):
    """Gjeresite k per te cilat zgjidhet problemi: nga w0-1 deri te 1 (shkalle gjeometrike)."""
    ks = set()
    for i in range(count):
        ks.add(max(1, round((w0 - 1) * (1 / max(1, w0 - 1)) ** (i / (count - 1)))))
    return sorted(ks, reverse=True)


def optimize(graph, method="sa", seconds=60.0, seed=0, count=12, log=print):
    """
    Nderton frontin Pareto:
      1. fillon nga renditja minimum degree (dhe nje e rastesishme);
      2. per secilen gjeresi k ekzekuton metaheuristiken, duke filluar nga
         permutacioni me i mire i arkivit per ate k (warm start);
      3. te gjitha permutacionet e pranuara shtohen ne arkiv.
    """
    rng = random.Random(seed)
    archive = Archive(graph)
    t0 = time.perf_counter()
    md = min_degree_order(graph)
    deg0 = out_degrees(graph, md)
    archive.add(md, width_profile(deg0))
    archive.add(random_order(graph, rng), width_profile(out_degrees(graph, random_order(graph, rng))))
    w0 = max(deg0)
    ks = width_targets(w0, count)
    log(f"minimum degree: gjeresia e plote {w0} ({time.perf_counter() - t0:.1f}s); "
        f"gjeresite k: {ks}")
    _, fn = METHODS[method]
    per_k = max(0.0, seconds - (time.perf_counter() - t0)) / len(ks)
    for k in ks:
        start = start_for(archive, k, md)
        _, size, iters, acc = fn(graph, k, start, per_k, archive, rng)
        log(f"  k={k:<4} torso me e madhe = {size:<5} iteracione = {iters:<6} te pranuara = {acc}")
    return archive


def start_for(archive, k, default):
    """Permutacioni i arkivit me torson me te madhe per gjeresi <= k."""
    best_t, best_p = None, None
    for wd, (t, perm) in archive.best.items():
        if wd <= k and (best_t is None or t < best_t):
            best_t, best_p = t, perm
    return list(best_p) if best_p is not None else default[:]
