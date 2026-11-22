"""
Krahasimi i metodave: backtracking i thjeshte (bt), forward checking + MRV (fc)
dhe MRV + propagim i plote (full) ne te gjitha enigmat.
"""

import argparse

from killer_sudoku import METHODS, solve, violations
from puzzles import PUZZLES, load


def main():
    ap = argparse.ArgumentParser(description="Krahasimi i metodave CSP")
    ap.add_argument("puzzles", nargs="*", default=list(PUZZLES),
                    help="enigmat (default: te gjitha)")
    ap.add_argument("-m", "--methods", nargs="+", default=list(METHODS), choices=METHODS)
    ap.add_argument("--node-limit", type=int, default=2_000_000)
    ap.add_argument("--timeout", type=float, default=60.0)
    args = ap.parse_args()

    print(f"{'Enigma':<10} {'Metoda':<26} {'Statusi':<16} {'Nyje':>11} "
          f"{'Backtracks':>11} {'Koha':>9}  Valid")
    for name in args.puzzles:
        puzzle = load(name)
        for m in args.methods:
            grid, s, _ = solve(puzzle, m, args.node_limit, args.timeout)
            valid = violations(puzzle, grid) == 0 if grid else "-"
            print(f"{name:<10} {METHODS[m]:<26} {s['status']:<16} {s['nodes']:>11,} "
                  f"{s['backtracks']:>11,} {s['time']:>8.3f}s  {valid}", flush=True)
        print()


if __name__ == "__main__":
    main()
