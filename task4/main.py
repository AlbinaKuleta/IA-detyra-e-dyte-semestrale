"""
Torso Decompositions - ekzekutimi i metaheuristikave dhe ruajtja e rezultateve.

Shembuj:
    python main.py --example                 # kontrollon shembullin e detyres
    python main.py easy -m sa --time 120     # Simulated Annealing ne grafin easy
    python main.py medium -m ils --time 120 --out results/medium_ils.json
"""

import argparse
import json
import os
import random
import time

from metaheuristics import METHODS, min_degree_order, optimize, random_order
from torso import (EXAMPLE_X, WIDTH_CAP, Archive, evaluate, example_graph,
                   hypervolume, load_graph, out_degrees, width_profile)

HERE = os.path.dirname(os.path.abspath(__file__))
PROBLEM_IDS = {"easy": "small-graph", "medium": "medium-graph", "hard": "large-graph"}


def load(name):
    path = os.path.join(HERE, "data", name + ".gr") if name in PROBLEM_IDS else name
    return load_graph(path)


def baseline(graph, kind, seed):
    archive = Archive(graph)
    t0 = time.perf_counter()
    perm = min_degree_order(graph) if kind == "mindeg" else random_order(graph, random.Random(seed))
    archive.add(perm, width_profile(out_degrees(graph, perm)))
    return archive, time.perf_counter() - t0


def report(graph, archive, k=20):
    chosen = archive.select(k)
    n = graph.n
    hv_all = archive.hv()
    hv_sel = hypervolume([(t, wd) for t, wd, _ in chosen], n)
    norm = n * WIDTH_CAP
    print(f"\nFronti Pareto: {len(archive.points())} pika jo te dominuara, "
          f"te zgjedhura {len(chosen)}")
    print(f"Hypervolume (ref = (t = {n}, width = {WIDTH_CAP})): "
          f"te gjitha = {hv_all / norm:.5f}, 20 te zgjedhurat = {hv_sel / norm:.5f}\n")
    print("   t   | torso size | torso width")
    for t, wd, perm in chosen:
        size, width = evaluate(graph, list(perm) + [t])     # rivleresim i pavarur
        assert (size, width) == (n - t, wd)
        print(f"{t:>6} | {size:>10} | {width:>11}")
    return chosen, hv_sel / norm


def main():
    ap = argparse.ArgumentParser(description="Torso Decompositions me metaheuristika")
    ap.add_argument("instance", nargs="?", default="easy",
                    help="easy, medium, hard ose rruga e nje skedari .gr")
    ap.add_argument("-m", "--method", default="sa", choices=list(METHODS) + ["mindeg", "random"],
                    help="sa (default), ils, mindeg ose random")
    ap.add_argument("--time", type=float, default=120.0, help="koha totale ne sekonda")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--targets", type=int, default=12, help="sa gjeresi k optimizohen")
    ap.add_argument("--out", help="ruaj 20 vektoret ne formatin JSON te dorezimit")
    ap.add_argument("--example", action="store_true", help="kontrollo shembullin e detyres")
    args = ap.parse_args()

    if args.example:
        g = example_graph()
        size, width = evaluate(g, EXAMPLE_X)
        print(f"Shembulli: x = {EXAMPLE_X}")
        print(f"outdeg sipas pozitave = {out_degrees(g, EXAMPLE_X[:-1])}")
        print(f"torso size = {size}, torso width = {width}   (pritet: 4 dhe 2)")
        return

    graph = load(args.instance)
    print(f"Grafi: {graph.name}  |  n = {graph.n}, brinje = {graph.m}  |  "
          f"metoda: {args.method}, koha {args.time:.0f}s, seed {args.seed}")
    t0 = time.perf_counter()
    if args.method in METHODS:
        archive = optimize(graph, args.method, args.time, args.seed, args.targets)
    else:
        archive, _ = baseline(graph, args.method, args.seed)
    elapsed = time.perf_counter() - t0
    chosen, hv = report(graph, archive)
    print(f"\nKoha: {elapsed:.1f}s")

    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        submission = [{
            "decisionVector": [list(perm) + [t] for t, _, perm in chosen],
            "problem": PROBLEM_IDS.get(graph.name, graph.name),
            "challenge": "spoc-3-torso-decompositions",
        }]
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(submission, f)
        print(f"Vektoret u ruajten ne {args.out}")


if __name__ == "__main__":
    main()
