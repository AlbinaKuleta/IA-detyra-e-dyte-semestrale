"""
Instancat e problemit te vendosjes se mysafireve.

- "shembull":     instance e vogel (12 mysafire, 3 tavolina x 4) ne formatin tekstual,
                  e mire per te pare formulen me --formula.
- "aheng":        instanca e detyres: 100 mysafire, 10 tavolina x 10, |B - G| <= 3,
                  150 cifte konflikti dhe 12 grupe qe ulen bashke (seed fiks).
- "aheng-i-veshtire": 100 mysafire me 600 konflikte dhe 20 grupe bashke.
- "unsat-grupi":  nje grup "bashke" permban nje cift konflikti -> pa zgjidhje.
- "unsat-gjinia": 30 mysafire (19 burra, 11 gra) ne 3 tavolina x 10; ne nje tavoline
                  hyjne te shumten 6 burra, pra gjithsej te shumten 18 -> pa zgjidhje.

Cdo instance mund te ruhet ne formatin tekstual me `python instances.py --write DIR`.
"""

import argparse
import os
import random

from seating_sat import Instance, parse_text

EXAMPLE = """\
# 12 mysafire, 3 tavolina me nga 4 karrige, |burra - gra| <= 2
tables 3 4
diff 2
guest M1 B
guest M2 G
guest M3 B
guest M4 G
guest M5 B
guest M6 G
guest M7 B
guest M8 G
guest M9 B
guest M10 G
guest M11 B
guest M12 G
conflict M1 M5
conflict M1 M3
conflict M2 M4
conflict M6 M8
conflict M9 M11
together M1 M2
together M5 M6 M10
"""


def generate(name, guests=100, tables=10, seats=10, max_diff=3, men=None,
             n_conflicts=150, n_groups=12, group_size=(2, 4), seed=0):
    rng = random.Random(seed)
    names = [f"M{i + 1}" for i in range(guests)]
    men = guests // 2 + 2 if men is None else men
    gender = ["B"] * men + ["G"] * (guests - men)
    rng.shuffle(gender)

    order = list(range(guests))
    rng.shuffle(order)
    together, pos = [], 0
    for _ in range(n_groups):
        size = rng.randint(*group_size)
        together.append(sorted(order[pos:pos + size]))
        pos += size
    group_of = {g: i for i, grp in enumerate(together) for g in grp}

    conflicts = set()
    while len(conflicts) < n_conflicts:
        a, b = sorted(rng.sample(range(guests), 2))
        if a in group_of and group_of.get(b) == group_of[a]:
            continue                      # nuk vendoset konflikt brenda nje grupi
        conflicts.add((a, b))
    return Instance(names, gender, tables, seats, max_diff, sorted(conflicts), together, name)


def unsat_group():
    inst = generate("unsat-grupi", seed=1)
    a, b = inst.together[0][:2]
    inst.conflicts.append((a, b))         # dy anetare te te njejtit grup ne konflikt
    return inst


INSTANCES = {
    "shembull": lambda: parse_text(EXAMPLE, "shembull"),
    "aheng": lambda: generate("aheng", seed=2026),
    "aheng-i-veshtire": lambda: generate("aheng-i-veshtire", n_conflicts=600, n_groups=20,
                                         seed=7),
    "unsat-grupi": unsat_group,
    "unsat-gjinia": lambda: generate("unsat-gjinia", guests=30, tables=3, men=19,
                                     n_conflicts=30, n_groups=2, seed=3),
}


def to_text(inst):
    lines = [f"tables {inst.tables} {inst.seats}", f"diff {inst.max_diff}"]
    lines += [f"guest {n} {g}" for n, g in zip(inst.names, inst.gender)]
    lines += [f"conflict {inst.names[a]} {inst.names[b]}" for a, b in inst.conflicts]
    lines += ["together " + " ".join(inst.names[g] for g in grp) for grp in inst.together]
    return "\n".join(lines) + "\n"


def load(name):
    if name in INSTANCES:
        return INSTANCES[name]()
    with open(name, encoding="utf-8") as f:
        return parse_text(f.read(), os.path.basename(name))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Instancat e vendosjes se mysafireve")
    ap.add_argument("--write", metavar="DIR", help="ruaj instancat si skedare .txt")
    args = ap.parse_args()
    if args.write:
        os.makedirs(args.write, exist_ok=True)
        for name in INSTANCES:
            path = os.path.join(args.write, name + ".txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(to_text(load(name)))
            print("u ruajt", path)
    else:
        for name in INSTANCES:
            i = load(name)
            print(f"{name:<18} G={i.guests} T={i.tables} S={i.seats} D={i.max_diff} "
                  f"B={i.gender.count('B')} konflikte={len(i.conflicts)} grupe={len(i.together)}")
