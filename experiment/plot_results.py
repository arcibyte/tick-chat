#!/usr/bin/env python3
"""Genera la gráfica del experimento a partir de results.csv.

Uso (desde la raíz del repo):
    python experiment/plot_results.py
    python experiment/plot_results.py --csv experiment/results.csv --out experiment/grafica

Requiere matplotlib (pip install matplotlib). Produce .png (300 dpi) y .pdf
vectorial, este último recomendado para el póster.
"""
import argparse
import csv
import math
import statistics as st
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
INK, MUTED, GRID = "#1f2937", "#6b7280", "#e5e7eb"
BLUE = "#2563eb"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", type=Path, default=ROOT / "experiment" / "results.csv")
    ap.add_argument("--out", type=Path, default=ROOT / "experiment" / "grafica")
    args = ap.parse_args()

    groups = defaultdict(list)
    n_msgs, lost, dups = None, 0, 0
    with open(args.csv) as f:
        for r in csv.DictReader(f):
            d = float(r["outage_s"])
            v = float(r["recovery_s"])
            if not math.isnan(v):
                groups[d].append(v)
            n_msgs = int(r["n_messages"])
            lost += int(r["lost"])
            dups += int(r["duplicates"])

    xs = sorted(groups)
    means = [st.mean(groups[x]) for x in xs]
    sds = [st.stdev(groups[x]) if len(groups[x]) > 1 else 0 for x in xs]

    fig, ax = plt.subplots(figsize=(7, 4.2))
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(MUTED)

    for x in xs:  # repeticiones individuales
        ax.scatter([x] * len(groups[x]), groups[x], s=28, color=BLUE, alpha=0.35,
                   zorder=3, linewidths=0)
    ax.errorbar(xs, means, yerr=sds, color=BLUE, linewidth=0, elinewidth=2, marker="o",
                markersize=7, markeredgecolor="white", markeredgewidth=2,
                capsize=4, zorder=4, label="Media ± desv. estándar (3 repeticiones)")

    ax.set_xlabel("Duración de la caída del servidor central (s)", color=INK)
    ax.set_ylabel("Tiempo de recuperación (s)", color=INK)
    ax.set_ylim(0, 2)
    ax.set_xticks(xs)
    ax.tick_params(colors=MUTED)
    ax.set_title(f"Entrega de {n_msgs} mensajes en cola tras recuperarse el central\n"
                 f"Mensajes perdidos: {lost} · duplicados: {dups}",
                 color=INK, fontsize=11, loc="left")
    ax.legend(frameon=False, labelcolor=INK, loc="upper center", bbox_to_anchor=(0.5, -0.17), ncol=1)
    fig.tight_layout()

    fig.savefig(args.out.with_suffix(".png"), dpi=300)
    fig.savefig(args.out.with_suffix(".pdf"))
    print(f"Guardado {args.out.with_suffix('.png')} y .pdf")
    for x, m, s in zip(xs, means, sds):
        print(f"  caída {x:>4g} s -> {m:6.3f} ± {s:5.3f} s")


if __name__ == "__main__":
    main()
