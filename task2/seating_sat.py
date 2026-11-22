"""
Vendosja e mysafireve ne tavolina - SAT.

G mysafire (p.sh. 100) duhet te ulen ne T tavolina (p.sh. 10) me nga S karrige.
Kushtet:
    1. Cdo mysafir ulet ne saktesisht nje tavoline.
    2. Ne cdo tavoline ulen te shumten S mysafire (me G = T*S: saktesisht S).
    3. Ciftet ne listen "konflikt" nuk ulen ne te njejten tavoline.
    4. Mysafiret ne listen "bashke" ulen ne te njejten tavoline.
    5. Ne cdo tavoline |burra - gra| <= D (p.sh. D = 3).

Variablat:  x(g, t) = "mysafiri g ulet ne tavolinen t"     (G*T variabla)

Formula ndertohet ne CNF (konjuksion klauzolash) dhe zgjidhet me solver-in
CDCL te sat_solver.py. Kushtet "te shumten k" (cardinality) kodohen me
numeruesin sekuencial (Sinz, 2005), qe shton variabla ndihmese.
"""

import argparse
import time

from sat_solver import check_model, solve


# ---------------------------------------------------------------------------
# Instanca
# ---------------------------------------------------------------------------

class Instance:
    """
    names    - emrat e mysafireve (M1, M2, ...)
    gender   - "B" (burre) ose "G" (grua) per cdo mysafir
    tables   - numri i tavolinave T,  seats - karriget per tavoline S
    max_diff - dallimi maksimal |burra - gra| ne nje tavoline (D)
    conflicts - ciftet (a, b) qe nuk ulen bashke (indekse nga 0)
    together  - grupet qe duhet te ulen ne te njejten tavoline
    """

    def __init__(self, names, gender, tables, seats, max_diff, conflicts, together, name=""):
        self.names = list(names)
        self.gender = list(gender)
        self.tables = tables
        self.seats = seats
        self.max_diff = max_diff
        self.conflicts = [tuple(p) for p in conflicts]
        self.together = [list(g) for g in together]
        self.name = name

    @property
    def guests(self):
        return len(self.names)

    def gender_bounds(self):
        """
        Me S karrige dhe |B - G| <= D, ku B + G = S:
            B - G = 2B - S  =>  -D <= 2B - S <= D  =>  (S - D)/2 <= B <= (S + D)/2
        Pra ne cdo tavoline te plote ka te shumten floor((S + D)/2) burra
        dhe te shumten floor((S + D)/2) gra.
        """
        return (self.seats + self.max_diff) // 2


def parse_text(text, name=""):
    """
    Formati tekstual (nje rresht per komande, # per koment):
        tables 10 10            # T tavolina me S karrige
        diff 3                  # |burra - gra| <= D
        guest M1 B              # emri dhe gjinia (B = burre, G = grua)
        conflict M1 M5          # M1 dhe M5 nuk ulen bashke
        together M2 M7 M9       # M2, M7, M9 ulen ne te njejten tavoline
    """
    names, gender, conflicts, together = [], [], [], []
    tables = seats = None
    diff = 0
    raw_conf, raw_tog = [], []
    for line in text.splitlines():
        parts = line.split("#")[0].split()
        if not parts:
            continue
        cmd, args = parts[0].lower(), parts[1:]
        if cmd == "tables":
            tables, seats = int(args[0]), int(args[1])
        elif cmd == "diff":
            diff = int(args[0])
        elif cmd == "guest":
            names.append(args[0])
            gender.append(args[1].upper())
        elif cmd == "conflict":
            raw_conf.append(args)
        elif cmd == "together":
            raw_tog.append(args)
        else:
            raise ValueError(f"komande e panjohur: {cmd}")
    index = {n: i for i, n in enumerate(names)}
    conflicts = [(index[a], index[b]) for a, b in raw_conf]
    together = [[index[x] for x in grp] for grp in raw_tog]
    return Instance(names, gender, tables, seats, diff, conflicts, together, name)


# ---------------------------------------------------------------------------
# Kodimi ne CNF
# ---------------------------------------------------------------------------

class Encoder:
    def __init__(self, inst, symmetry=True):
        self.inst = inst
        self.symmetry = symmetry
        self.num_vars = inst.guests * inst.tables
        self.clauses = []
        self.groups = {}          # emri i kushtit -> [klauzola, variabla ndihmese]
        self.samples = {}         # emri i kushtit -> klauzolat e para (per shfaqje)

    def x(self, g, t):
        """Variabla x(g, t): mysafiri g ne tavolinen t (numra 1 .. G*T)."""
        return g * self.inst.tables + t + 1

    def new_var(self):
        self.num_vars += 1
        return self.num_vars

    def _add(self, group, clause):
        entry = self.groups.setdefault(group, [0, 0])
        entry[0] += 1
        self.clauses.append(clause)
        sample = self.samples.setdefault(group, [])
        if len(sample) < 8:
            sample.append(clause)

    def _aux(self, group, count):
        self.groups.setdefault(group, [0, 0])[1] += count

    def at_most(self, lits, k, group):
        """
        Numeruesi sekuencial (Sinz 2005): sum(lits) <= k.
        s(i, j) = "nder i+1 literalet e para, te pakten j+1 jane te vertete".
        """
        n = len(lits)
        if k >= n:
            return
        if k == 0:
            for l in lits:
                self._add(group, [-l])
            return
        s = [[self.new_var() for _ in range(k)] for _ in range(n - 1)]
        self._aux(group, (n - 1) * k)
        self._add(group, [-lits[0], s[0][0]])
        for j in range(1, k):
            self._add(group, [-s[0][j]])
        for i in range(1, n - 1):
            self._add(group, [-lits[i], s[i][0]])
            self._add(group, [-s[i - 1][0], s[i][0]])
            for j in range(1, k):
                self._add(group, [-lits[i], -s[i - 1][j - 1], s[i][j]])
                self._add(group, [-s[i - 1][j], s[i][j]])
            self._add(group, [-lits[i], -s[i - 1][k - 1]])
        self._add(group, [-lits[n - 1], -s[n - 2][k - 1]])

    def encode(self):
        inst = self.inst
        G, T = inst.guests, inst.tables
        x = self.x

        # (1) cdo mysafir ne te pakten nje tavoline
        for g in range(G):
            self._add("1a. te pakten nje tavoline", [x(g, t) for t in range(T)])
        # (1) ... dhe ne te shumten nje (pairwise)
        for g in range(G):
            for t1 in range(T):
                for t2 in range(t1 + 1, T):
                    self._add("1b. te shumten nje tavoline", [-x(g, t1), -x(g, t2)])

        # (2) kapaciteti i tavolines
        for t in range(T):
            self.at_most([x(g, t) for g in range(G)], inst.seats, "2. kapaciteti i tavolines")

        # (3) konfliktet
        for a, b in inst.conflicts:
            for t in range(T):
                self._add("3. konfliktet", [-x(a, t), -x(b, t)])

        # (4) grupet bashke: x(a, t) <-> x(b, t) per anetaret e njepasnjeshem
        for grp in inst.together:
            for a, b in zip(grp, grp[1:]):
                for t in range(T):
                    self._add("4. bashke", [-x(a, t), x(b, t)])
                    self._add("4. bashke", [-x(b, t), x(a, t)])

        # (5) gjinia: te shumten floor((S + D)/2) burra dhe po aq gra ne tavoline
        hi = inst.gender_bounds()
        men = [g for g in range(G) if inst.gender[g] == "B"]
        women = [g for g in range(G) if inst.gender[g] == "G"]
        for t in range(T):
            self.at_most([x(g, t) for g in men], hi, "5. gjinia (burra)")
            self.at_most([x(g, t) for g in women], hi, "5. gjinia (gra)")

        # thyerja e simetrise: tavolinat jane identike, mysafiri i pare ne tavolinen 1
        if self.symmetry and G > 0:
            self._add("6. simetria", [x(0, 0)])

        return self.num_vars, self.clauses


def quick_checks(inst):
    """
    Kontrolle te shpejta (numerim) para SAT-it. Nese ndonje deshton, formula
    me siguri nuk ka zgjidhje. SAT solver-i e gjen kete vete, por per disa
    raste (p.sh. shume burra) prova me rezolucion mund te jete shume e gjate.
    """
    notes = []
    hi = inst.gender_bounds()
    if inst.guests > inst.tables * inst.seats:
        notes.append(f"{inst.guests} mysafire > {inst.tables} x {inst.seats} karrige")
    for label, sex in (("burra", "B"), ("gra", "G")):
        cnt = inst.gender.count(sex)
        if cnt > inst.tables * hi:
            notes.append(f"{cnt} {label} > {inst.tables} tavolina x {hi} {label} per tavoline")
    group_of = {g: i for i, grp in enumerate(inst.together) for g in grp}
    for grp in inst.together:
        if len(grp) > inst.seats:
            notes.append(f"nje grup bashke ka {len(grp)} > {inst.seats} mysafire")
    for a, b in inst.conflicts:
        if a in group_of and group_of.get(b) == group_of[a]:
            notes.append(f"{inst.names[a]} dhe {inst.names[b]} jane ne konflikt, "
                         f"por duhet te ulen bashke")
    return notes


def to_dimacs(num_vars, clauses):
    lines = [f"p cnf {num_vars} {len(clauses)}"]
    lines += [" ".join(map(str, c)) + " 0" for c in clauses]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Dekodimi dhe verifikimi
# ---------------------------------------------------------------------------

def decode(inst, enc, model):
    """seating[g] = tavolina e mysafirit g."""
    seating = []
    for g in range(inst.guests):
        tables = [t for t in range(inst.tables) if model[enc.x(g, t)]]
        seating.append(tables[0] if len(tables) == 1 else None)
    return seating


def violations(inst, seating):
    """
    Objective function: numri i kushteve te shkelura, i llogaritur direkt nga
    caktimi (pa formulen). 0 = te gjitha kushtet plotesohen.
    """
    bad = []
    for g, t in enumerate(seating):
        if t is None:
            bad.append(f"{inst.names[g]} nuk ka saktesisht nje tavoline")
    for t in range(inst.tables):
        at = [g for g, tt in enumerate(seating) if tt == t]
        if len(at) > inst.seats:
            bad.append(f"tavolina {t + 1} ka {len(at)} mysafire")
        b = sum(inst.gender[g] == "B" for g in at)
        gr = sum(inst.gender[g] == "G" for g in at)
        if abs(b - gr) > inst.max_diff:
            bad.append(f"tavolina {t + 1}: |{b} - {gr}| > {inst.max_diff}")
    for a, b in inst.conflicts:
        if seating[a] is not None and seating[a] == seating[b]:
            bad.append(f"{inst.names[a]} dhe {inst.names[b]} jane bashke")
    for grp in inst.together:
        if len({seating[g] for g in grp}) != 1:
            bad.append("grupi " + ", ".join(inst.names[g] for g in grp) + " eshte ndare")
    return bad


def format_seating(inst, seating):
    lines = []
    for t in range(inst.tables):
        at = [g for g, tt in enumerate(seating) if tt == t]
        b = sum(inst.gender[g] == "B" for g in at)
        gr = len(at) - b
        guests = " ".join(f"{inst.names[g]}({inst.gender[g]})" for g in at)
        lines.append(f"Tavolina {t + 1:>2} [{len(at):>2} | B={b} G={gr}]: {guests}")
    return "\n".join(lines)


def format_formula(inst, enc, limit=6):
    """Shfaq disa klauzola te secilit kusht me emrat e variablave."""
    names = {enc.x(g, t): f"x({inst.names[g]},T{t + 1})"
             for g in range(inst.guests) for t in range(inst.tables)}

    def lit(l):
        n = names.get(abs(l), f"s{abs(l)}")
        return n if l > 0 else "~" + n

    out = []
    for group, (count, aux) in enc.groups.items():
        out.append(f"{group}: {count:,} klauzola" + (f", {aux:,} variabla ndihmese" if aux else ""))
        for c in enc.samples[group][:limit]:
            out.append("    (" + " v ".join(lit(l) for l in c) + ")")
        if count > limit:
            out.append("    ...")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main():
    from instances import INSTANCES, load

    ap = argparse.ArgumentParser(description="Vendosja e mysafireve ne tavolina me SAT")
    ap.add_argument("instance", nargs="?", default="aheng",
                    help="emri i instances (shih --list) ose rruga e nje skedari .txt")
    ap.add_argument("--list", action="store_true", help="shfaq instancat")
    ap.add_argument("--formula", action="store_true",
                    help="shfaq klauzolat e formules sipas kushteve")
    ap.add_argument("--dimacs", metavar="FILE", help="ruaj formulen ne formatin DIMACS")
    ap.add_argument("--no-symmetry", action="store_true",
                    help="pa thyerjen e simetrise se tavolinave")
    ap.add_argument("--timeout", type=float, default=300.0)
    args = ap.parse_args()

    if args.list:
        for name in INSTANCES:
            i = load(name)
            print(f"{name:<18} G={i.guests:<4} T={i.tables:<3} S={i.seats:<3} D={i.max_diff} "
                  f"konflikte={len(i.conflicts):<4} grupe bashke={len(i.together)}")
        return

    inst = load(args.instance)
    b = inst.gender.count("B")
    print(f"Instanca: {inst.name}  |  {inst.guests} mysafire (B={b}, G={inst.guests - b}), "
          f"{inst.tables} tavolina x {inst.seats} karrige, |B - G| <= {inst.max_diff}")
    print(f"Konflikte: {len(inst.conflicts)}  |  grupe bashke: {len(inst.together)}\n")

    for note in quick_checks(inst):
        print(f"Kontroll paraprak: {note} -> pritet UNSAT")

    t0 = time.perf_counter()
    enc = Encoder(inst, symmetry=not args.no_symmetry)
    num_vars, clauses = enc.encode()
    t_enc = time.perf_counter() - t0
    print(f"Formula CNF: {num_vars:,} variabla ({inst.guests * inst.tables:,} x(g,t) + "
          f"{num_vars - inst.guests * inst.tables:,} ndihmese), {len(clauses):,} klauzola "
          f"({t_enc:.2f}s)")
    if args.formula:
        print("\n" + format_formula(inst, enc))
    else:
        for group, (count, aux) in enc.groups.items():
            extra = f", {aux:,} ndihmese" if aux else ""
            print(f"  {group:<30} {count:>7,} klauzola{extra}")
    if args.dimacs:
        with open(args.dimacs, "w", encoding="utf-8") as f:
            f.write(to_dimacs(num_vars, clauses))
        print(f"\nFormula u ruajt ne {args.dimacs}")

    print()
    try:
        sat, model, stats = solve(num_vars, clauses, args.timeout)
    except TimeoutError:
        print(f"Timeout pas {args.timeout}s")
        return
    print(f"Rezultati: {'SAT - u gjet vendosje' if sat else 'UNSAT - nuk ka vendosje'}")
    print(f"Vendime: {stats['decisions']:,} | propagime: {stats['propagations']:,} | "
          f"konflikte: {stats['conflicts']:,} | restarte: {stats['restarts']} | "
          f"koha: {stats['time']:.2f}s")
    if sat:
        seating = decode(inst, enc, model)
        print("\n" + format_seating(inst, seating))
        bad = violations(inst, seating)
        print(f"\nFormula e plotesuar = {check_model(clauses, model)} | "
              f"kushte te shkelura = {len(bad)} | valid = {not bad}")
        for v in bad:
            print("  -", v)


if __name__ == "__main__":
    main()
