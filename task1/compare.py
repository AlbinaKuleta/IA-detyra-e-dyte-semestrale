"""
Krahasimi i heuristikave: ekzekuton A* me secilen heuristike ne te gjitha
instancat dhe shfaq nyjet e zgjeruara, nyjet e prera dhe kohen.
"""

import argparse

from blocked_queens import HEURISTICS, astar, is_valid
from instances import INSTANCES, load


def main():
    ap = argparse.ArgumentParser(description="Krahasimi i heuristikave te A*")
    ap.add_argument("instances", nargs="*", default=list(INSTANCES),
                    help="instancat (default: te gjitha)")
    ap.add_argument("--node-limit", type=int, default=100_000)
    ap.add_argument("--timeout", type=float, default=20.0)
    ap.add_argument("--order", nargs="+", default=["row", "mrv"], choices=["row", "mrv"],
                    help="renditja e rreshtave: row (me radhe) dhe/ose mrv (default: te dyja)")
    args = ap.parse_args()

    for order in args.order:
        print(f"=== Renditja e rreshtave: {order} ===\n")
        print(f"{'Instanca':<10} {'Heuristika':<24} {'Statusi':<16} {'Zgjeruara':>10} "
              f"{'Prera':>9} {'Open max':>10} {'Koha':>8}  Valid")
        for name in args.instances:
            inst = load(name)
            for key, (label, h, _) in HEURISTICS.items():
                sol, s = astar(inst, h, order, args.node_limit, args.timeout)
                valid = is_valid(inst, sol) if sol is not None else "-"
                print(f"{name:<10} {label:<24} {s['status']:<16} {s['expanded']:>10,} "
                      f"{s['pruned']:>9,} {s['max_open']:>10,} {s['time']:>7.2f}s  {valid}",
                      flush=True)
            print()

if __name__ == "__main__":
    main()
