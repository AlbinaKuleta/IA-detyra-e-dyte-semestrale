"""
Gjeneratori i enigmave Killer Sudoku.

1. Gjenerohet nje rrjete e plote valide sudoku (backtracking me renditje te rastesishme).
2. Rrjeta ndahet ne kafaze: nga nje qelize e lire rritet kafazi me fqinje
   ortogonale te rastesishem, pa perseritur numer brenda kafazit.
3. Shuma e cdo kafazi llogaritet nga rrjeta.
4. Me solver-in CSP kerkohen deri ne 2 zgjidhje. Nese ka 2, kafazi i nje
   qelize ku ato dallojne ndahet me dysh, dhe kontrolli perseritet derisa
   zgjidhja te jete unike.

Perdorimi:  python generator.py --level hard --seed 1
"""

import argparse
import random

from killer_sudoku import PEERS, Puzzle, solve, to_map

LEVELS = {                      # madhesia e kafazeve (min, max)
    "easy": (1, 3),
    "medium": (2, 4),
    "hard": (2, 5),
    "expert": (3, 6),
}


def random_grid(rng):
    grid = [0] * 81

    def fill(i):
        if i == 81:
            return True
        vals = list(range(1, 10))
        rng.shuffle(vals)
        for v in vals:
            if all(grid[p] != v for p in PEERS[i]):
                grid[i] = v
                if fill(i + 1):
                    return True
        grid[i] = 0
        return False

    fill(0)
    return grid


def random_cages(grid, sizes, rng):
    owner = [None] * 81
    cages = []
    order = list(range(81))
    rng.shuffle(order)
    for start in order:
        if owner[start] is not None:
            continue
        target = rng.randint(*sizes)
        cells, used = [start], {grid[start]}
        owner[start] = len(cages)
        while len(cells) < target:
            frontier = []
            for i in cells:
                r, c = divmod(i, 9)
                for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                    j = nr * 9 + nc
                    if 0 <= nr < 9 and 0 <= nc < 9 and owner[j] is None \
                            and grid[j] not in used:
                        frontier.append(j)
            if not frontier:
                break
            j = rng.choice(frontier)
            owner[j] = len(cages)
            cells.append(j)
            used.add(grid[j])
        cages.append((sum(grid[i] for i in cells), cells))
    return cages


def neighbors(i):
    r, c = divmod(i, 9)
    for nr, nc in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
        if 0 <= nr < 9 and 0 <= nc < 9:
            yield nr * 9 + nc


def components(cells):
    """Ndan nje bashkesi qelizash ne pjese te lidhura (ortogonalisht)."""
    left, parts = set(cells), []
    while left:
        stack = [left.pop()]
        part = []
        while stack:
            i = stack.pop()
            part.append(i)
            for j in neighbors(i):
                if j in left:
                    left.remove(j)
                    stack.append(j)
        parts.append(part)
    return parts


def split_at(cages, grid, cell, rng):
    """
    Kafazi qe permban `cell` ndahet: `cell` bashke me nje fqinj te tij nga i
    njejti kafaz formojne kafaz te ri, pjesa tjeter ndahet ne pjese te lidhura.
    """
    ci = next(k for k, (_, cells) in enumerate(cages) if cell in cells)
    cells = cages.pop(ci)[1]
    same = [j for j in neighbors(cell) if j in cells]
    new = [cell] + ([rng.choice(same)] if len(cells) > 2 and same else [])
    rest = [i for i in cells if i not in new]
    for part in [new] + components(rest):
        cages.append((sum(grid[i] for i in part), part))


def generate(level, seed, max_grids=50, timeout=30.0):
    """
    Kthen (enigma, zgjidhja, numri i ndarjeve). Nese enigma ka me shume se nje
    zgjidhje, ndahet kafazi i nje qelize ku dy zgjidhjet dallojne dhe provohet
    perseri, derisa zgjidhja te jete unike.
    """
    rng = random.Random(seed)
    for _ in range(max_grids):
        grid = random_grid(rng)
        cages = random_cages(grid, LEVELS[level], rng)
        splits = 0
        while True:
            puzzle = Puzzle(cages)
            _, stats, sols = solve(puzzle, "full", timeout=timeout, count_limit=2)
            if stats["status"] != "zgjidhje":
                break                   # timeout -> provohet rrjete tjeter
            if len(sols) == 1:
                return puzzle, grid, splits
            diff = [i for i in range(81) if sols[0][i] != sols[1][i]]
            split_at(cages, grid, rng.choice(diff), rng)
            splits += 1
    return None, None, 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Gjeneratori i Killer Sudoku")
    ap.add_argument("--level", default="medium", choices=LEVELS)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    puzzle, grid, splits = generate(args.level, args.seed)
    if puzzle is None:
        print("Nuk u gjet enigme me zgjidhje unike.")
    else:
        sizes = [len(c) for _, c in puzzle.cages]
        print(f"# niveli {args.level}, seed {args.seed}, {len(sizes)} kafaze, "
              f"madhesia {min(sizes)}-{max(sizes)}, ndarje {splits}")
        print(to_map(puzzle))
