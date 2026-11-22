"""
Instancat e Blocked N-Queens.

- "example": shembulli nga pershkrimi i ASP Competition (N = 4).
- "nX-pY":   instanca te gjeneruara me fare (seed) fiks: tabela N x N ku
             rreth Y% e katroreve jane te bllokuar ne menyre te rastesishme.
- "unsat6":  instance e vogel pa zgjidhje (per te treguar se A* e verteton kete).
             Edhe "n16-p60" nuk ka zgjidhje.

Cdo instance mund te ruhet ne formatin ASP me `python instances.py --write`.
"""

import argparse
import os
import random

from blocked_queens import Instance, parse_asp

EXAMPLE = "num(1). num(2). num(3). num(4). block(1,1). block(2,2). block(4,3)."


def generate(n, percent, seed):
    rng = random.Random(seed)
    cells = [(r, c) for r in range(n) for c in range(n)]
    k = round(n * n * percent / 100)
    return Instance(n, rng.sample(cells, k), f"n{n}-p{percent}")


def unsat6():
    # Diagonalja kryesore dhe ajo anesore e bllokuar ne gjysmen e siperme:
    # rreshti 1 ka vetem 2 katrore te lire, dhe asnje prej tyre nuk con ne zgjidhje.
    blocked = [(0, c) for c in range(6) if c not in (0, 5)]
    blocked += [(1, 2), (1, 3)]
    return Instance(6, blocked, "unsat6")


INSTANCES = {
    "example": lambda: parse_asp(EXAMPLE, "example"),
    "unsat6": unsat6,
    "n8-p10": lambda: generate(8, 10, 1),
    "n16-p40": lambda: generate(16, 40, 1),
    "n16-p60": lambda: generate(16, 60, 1),
    "n24-p50": lambda: generate(24, 50, 0),
    "n32-p55": lambda: generate(32, 55, 1),
    "n48-p50": lambda: generate(48, 50, 2),
    "n64-p50": lambda: generate(64, 50, 3),
}


def load(name):
    if name in INSTANCES:
        return INSTANCES[name]()
    with open(name, encoding="utf-8") as f:
        return parse_asp(f.read(), os.path.basename(name))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Instancat e Blocked N-Queens")
    ap.add_argument("--write", metavar="DIR", nargs="?", const="instances",
                    help="ruaj instancat ne formatin ASP (.lp) ne dosjen DIR")
    args = ap.parse_args()
    if args.write:
        os.makedirs(args.write, exist_ok=True)
        for name in INSTANCES:
            path = os.path.join(args.write, name + ".lp")
            with open(path, "w", encoding="utf-8") as f:
                f.write(load(name).to_asp())
            print("u ruajt", path)
    else:
        for name in INSTANCES:
            inst = load(name)
            print(f"{name:<10} N={inst.n:<3} te bllokuar={len(inst.blocked)}")
