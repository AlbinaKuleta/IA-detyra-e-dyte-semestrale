"""
SAT solver CDCL (Conflict-Driven Clause Learning), pa librari te jashtme.

Formula jepet ne CNF: lista klauzolash, ku cdo klauzole eshte lista literalesh
(int). Literali  v  do te thote "variabla v eshte e vertete", -v "eshte e rreme"
(si ne formatin DIMACS).

Teknikat:
    - Unit propagation me 2 literale te vezhguara (two watched literals)
    - Analiza e konfliktit 1-UIP dhe mesimi i klauzolave (clause learning)
    - Backjumping jo-kronologjik
    - VSIDS: zgjidhet variabla me aktivitet me te madh ne konflikte
    - Phase saving dhe restarte sipas sekuences Luby
"""

import heapq
import time


def luby(i):
    """Elementi i i-te (nga 1) i sekuences Luby: 1 1 2 1 1 2 4 1 1 2 ..."""
    k = 1
    while (1 << k) - 1 < i:
        k += 1
    while (1 << k) - 1 != i:
        i -= (1 << (k - 1)) - 1
        k = 1
        while (1 << k) - 1 < i:
            k += 1
    return 1 << (k - 1)


class CDCLSolver:
    def __init__(self, num_vars, clauses):
        self.n = num_vars
        self.clauses = []                       # klauzolat (origjinale + te mesuara)
        self.watches = [[] for _ in range(2 * num_vars + 2)]
        self.val = [0] * (num_vars + 1)         # 1 e vertete, -1 e rreme, 0 e pacaktuar
        self.level = [0] * (num_vars + 1)
        self.reason = [None] * (num_vars + 1)   # klauzola qe e detyroi vleren
        self.trail = []
        self.trail_lim = []
        self.qhead = 0
        self.activity = [0.0] * (num_vars + 1)
        self.var_inc = 1.0
        self.phase = [False] * (num_vars + 1)   # vlera e fundit (phase saving)
        self.heap = [(0.0, v) for v in range(1, num_vars + 1)]
        self.seen = [False] * (num_vars + 1)
        self.ok = True
        self.stats = {"decisions": 0, "propagations": 0, "conflicts": 0,
                      "learned": 0, "restarts": 0, "time": 0.0}
        for c in clauses:
            if not self._add_clause(c):
                self.ok = False
                break

    # -- ndihmese --------------------------------------------------------------

    @staticmethod
    def _idx(lit):
        return 2 * lit if lit > 0 else -2 * lit + 1

    def _value(self, lit):
        v = self.val[abs(lit)]
        return v if lit > 0 else -v

    def _decision_level(self):
        return len(self.trail_lim)

    def _enqueue(self, lit, reason):
        v = abs(lit)
        self.val[v] = 1 if lit > 0 else -1
        self.level[v] = self._decision_level()
        self.reason[v] = reason
        self.trail.append(lit)

    def _add_clause(self, lits):
        lits = list(dict.fromkeys(lits))
        if any(-l in lits for l in lits):
            return True                         # tautologji, gjithmone e vertete
        if not lits:
            return False
        if len(lits) == 1:
            value = self._value(lits[0])
            if value == -1:
                return False
            if value == 0:
                self._enqueue(lits[0], None)
            return True
        ci = len(self.clauses)
        self.clauses.append(lits)
        self.watches[self._idx(lits[0])].append(ci)
        self.watches[self._idx(lits[1])].append(ci)
        return True

    # -- unit propagation ---------------------------------------------------------

    def _propagate(self):
        """Kthen indeksin e klauzoles ne konflikt, ose None."""
        while self.qhead < len(self.trail):
            p = self.trail[self.qhead]
            self.qhead += 1
            self.stats["propagations"] += 1
            false_lit = -p
            ws = self.watches[self._idx(false_lit)]
            kept = []
            k = 0
            while k < len(ws):
                ci = ws[k]
                k += 1
                c = self.clauses[ci]
                if c[0] == false_lit:
                    c[0], c[1] = c[1], c[0]
                first = c[0]
                if self._value(first) == 1:
                    kept.append(ci)
                    continue
                for m in range(2, len(c)):
                    if self._value(c[m]) != -1:     # gjendet literal i ri per t'u vezhguar
                        c[1], c[m] = c[m], c[1]
                        self.watches[self._idx(c[1])].append(ci)
                        break
                else:
                    kept.append(ci)
                    if self._value(first) == -1:    # te gjithe literalet false -> konflikt
                        kept.extend(ws[k:])
                        self.watches[self._idx(false_lit)] = kept
                        self.qhead = len(self.trail)
                        return ci
                    self._enqueue(first, ci)        # klauzole unit -> detyrohet vlera
            self.watches[self._idx(false_lit)] = kept
        return None

    # -- analiza e konfliktit -----------------------------------------------------

    def _bump(self, v):
        self.activity[v] += self.var_inc
        if self.activity[v] > 1e100:
            for u in range(1, self.n + 1):
                self.activity[u] *= 1e-100
            self.var_inc *= 1e-100
            self.heap = [(-self.activity[u], u) for u in range(1, self.n + 1)
                         if self.val[u] == 0]
            heapq.heapify(self.heap)
        elif self.val[v] == 0:
            heapq.heappush(self.heap, (-self.activity[v], v))

    def _analyze(self, confl):
        """Analiza 1-UIP: kthen (klauzola e mesuar, niveli i backjump)."""
        learnt = [None]
        counter = 0
        p = None
        i = len(self.trail) - 1
        cur = self._decision_level()
        c = self.clauses[confl]
        while True:
            for q in (c if p is None else c[1:]):
                v = abs(q)
                if not self.seen[v] and self.level[v] > 0:
                    self.seen[v] = True
                    self._bump(v)
                    if self.level[v] == cur:
                        counter += 1
                    else:
                        learnt.append(q)
            while not self.seen[abs(self.trail[i])]:
                i -= 1
            p = self.trail[i]
            i -= 1
            self.seen[abs(p)] = False
            counter -= 1
            if counter == 0:
                break
            c = self.clauses[self.reason[abs(p)]]
        learnt[0] = -p
        for q in learnt[1:]:
            self.seen[abs(q)] = False

        if len(learnt) == 1:
            return learnt, 0
        best = max(range(1, len(learnt)), key=lambda j: self.level[abs(learnt[j])])
        learnt[1], learnt[best] = learnt[best], learnt[1]
        return learnt, self.level[abs(learnt[1])]

    def _cancel_until(self, lvl):
        if self._decision_level() <= lvl:
            return
        start = self.trail_lim[lvl]
        for lit in self.trail[start:]:
            v = abs(lit)
            self.phase[v] = lit > 0
            self.val[v] = 0
            self.reason[v] = None
            heapq.heappush(self.heap, (-self.activity[v], v))
        del self.trail[start:]
        del self.trail_lim[lvl:]
        self.qhead = len(self.trail)

    def _pick_branch(self):
        while self.heap:
            _, v = heapq.heappop(self.heap)
            if self.val[v] == 0:
                return v if self.phase[v] else -v
        return None

    # -- zgjidhja -----------------------------------------------------------------

    def solve(self, timeout=None):
        """Kthen (True, modeli) nese formula plotesohet, (False, None) nese jo.
        Ngre TimeoutError nese kalon koha."""
        t0 = time.perf_counter()
        try:
            if not self.ok or self._propagate() is not None:
                return False, None
            restart_no = 1
            limit = 100 * luby(restart_no)
            conflicts_here = 0
            while True:
                confl = self._propagate()
                if confl is not None:
                    self.stats["conflicts"] += 1
                    conflicts_here += 1
                    if self._decision_level() == 0:
                        return False, None          # konflikt pa asnje vendim -> UNSAT
                    learnt, back = self._analyze(confl)
                    self._cancel_until(back)
                    if len(learnt) == 1:
                        self._enqueue(learnt[0], None)
                    else:
                        ci = len(self.clauses)
                        self.clauses.append(learnt)
                        self.watches[self._idx(learnt[0])].append(ci)
                        self.watches[self._idx(learnt[1])].append(ci)
                        self._enqueue(learnt[0], ci)
                    self.stats["learned"] += 1
                    self.var_inc /= 0.95
                    if timeout is not None and (self.stats["conflicts"] & 0xFF) == 0 \
                            and time.perf_counter() - t0 > timeout:
                        raise TimeoutError
                else:
                    if conflicts_here >= limit:     # restart
                        self.stats["restarts"] += 1
                        restart_no += 1
                        limit = 100 * luby(restart_no)
                        conflicts_here = 0
                        self._cancel_until(0)
                        continue
                    lit = self._pick_branch()
                    if lit is None:                 # te gjitha variablat jane caktuar
                        model = [False] + [self.val[v] == 1 for v in range(1, self.n + 1)]
                        return True, model
                    self.stats["decisions"] += 1
                    self.trail_lim.append(len(self.trail))
                    self._enqueue(lit, None)
        finally:
            self.stats["time"] = time.perf_counter() - t0


def solve(num_vars, clauses, timeout=None):
    solver = CDCLSolver(num_vars, clauses)
    sat, model = solver.solve(timeout)
    return sat, model, solver.stats


def check_model(clauses, model):
    """Kontrollon qe cdo klauzole ka te pakten nje literal te vertete."""
    return all(any(model[l] if l > 0 else not model[-l] for l in c) for c in clauses)
