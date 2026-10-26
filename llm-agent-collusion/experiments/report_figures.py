"""Report figures. Usage: .venv/bin/python experiments/report_figures.py
Writes results/fig1_levers.png and results/fig2_entrants.png.
"""
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import report_stats
from report_stats import RESULTS, boot_ci, load, mean

BLUE, ORANGE, AQUA, YELLOW = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
INK, INK2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3df", "#fcfcfb"

plt.rcParams.update({
    "font.size": 10, "axes.edgecolor": INK2, "axes.labelcolor": INK, "xtick.color": INK2,
    "ytick.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
})


def paired(control_tag, tag):
    ctrl, cond = load(control_tag), load(tag)
    pairs = [(ctrl[s], cond[s]) for s in sorted(set(ctrl) & set(cond))]
    pct = lambda ps: (mean([k["index"] - c["index"] for k, c in ps])
                      / mean([k["index"] for k, _ in ps]) * 100)
    lost = [k["trades"] - c["trades"] for k, c in pairs]
    return pct(pairs), boot_ci(pairs, pct), mean(lost), boot_ci(lost, mean), len(pairs)


def fig1():
    levers = [  # (label, tag, family)
        ("Seller temperature 1.2", "c5_sellertemp", "comm"),
        ("Message cap (5 chars)", "c2_msgcap", "comm"),
        ("Overseer + gag", "c3_overseer", "comm"),
        ("No messaging", "c1_nomsg", "comm"),
        ("Ex-post fines, threshold 4", "expost_corrected", "comm"),
        ("Immediate fines, threshold 4", "immediate_corrected", "comm"),
        ("Ex-post fines, threshold 1", "expost_thresh1_boss", "comm"),
        ("Immediate fines, threshold 1", "immediate_thresh1_boss", "comm"),
        ("Partial transparency", "partial_transparency_boss", "info"),
        ("Dark book", "dark_book_comms", "info"),
        ("Sequential asks", "sequential_asks_boss", "info"),
        ("No-regret entrant x1", "c9_noregret1", "entrant"),
        ("Random entrant x1", "c8_random", "entrant"),
        ("Random entrant x2", "c8b_random2", "entrant"),
        ("No-regret + random", "c11_mixed", "entrant"),
        ("No-regret entrant x2", "c10_noregret2", "entrant"),
    ]
    style = {"comm": (BLUE, "o"), "info": (AQUA, "D"), "entrant": (ORANGE, "s")}
    rows = [(lab, fam, *paired("control41", tag)) for lab, tag, fam in levers]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.6, 5.6), sharey=True,
                                 gridspec_kw={"width_ratios": [1.4, 1], "wspace": 0.08})
    for i, (lab, fam, p, (plo, phi), l, (llo, lhi), n) in enumerate(rows):
        col, mk = style[fam]
        a1.plot([plo, phi], [i, i], color=col, lw=2, solid_capstyle="round")
        a1.plot(p, i, mk, color=col, ms=7, mec=SURFACE, mew=2)
        a1.text(292, i, f"{p:.0f}%  n={n}", va="center", ha="right", fontsize=8, color=INK2)
        a2.plot([llo, lhi], [i, i], color=col, lw=2, solid_capstyle="round")
        a2.plot(l, i, mk, color=col, ms=7, mec=SURFACE, mew=2)
    a1.set_yticks(range(len(rows)), [r[0] for r in rows])
    a1.invert_yaxis()
    a1.axvline(0, color=INK2, lw=1)
    a1.axvline(50, color=INK2, lw=1, ls=(0, (3, 3)))
    a1.text(51, -0.6, "50%", fontsize=8, color=INK2)
    a1.set_xlim(-10, 295)
    a1.set_xticks([0, 50, 100, 150, 200])
    a1.set_xlabel("Collusion removed, % of control (95% CI)")
    a2.axvline(0, color=INK2, lw=1)
    a2.set_xlabel("Lost trades per run vs. control (95% CI)")
    for a in (a1, a2):
        a.grid(axis="x", color=GRID, lw=0.8)
        a.set_axisbelow(True)
    a1.plot([], [], "o", color=BLUE, ms=7, label="Restrict or police speech")
    a1.plot([], [], "D", color=AQUA, ms=7, label="Restrict what sellers see")
    a1.plot([], [], "s", color=ORANGE, ms=7, label="Independent entrants")
    fig.legend(loc="upper center", ncol=3, frameon=False, bbox_to_anchor=(0.55, 1.01))
    fig.savefig(RESULTS / "fig1_levers.png", dpi=200, bbox_inches="tight")


def fig2():
    sizes = [  # (label, colour, marker, {n_entrants: tag})
        ("5x5", BLUE, "o", {0: "control41", 1: "c9_noregret1", 2: "c10_noregret2"}),
        ("7x7", ORANGE, "s", {0: "q7_control", 1: "q7_noregret1", 2: "q7_noregret2", 3: "q7_noregret3"}),
        ("9x9", AQUA, "D", {0: "q9_control", 1: "q9_noregret1", 2: "q9_noregret2", 3: "q9_noregret3"}),
        ("15x15", YELLOW, "^", {0: "q15_control", 1: "q15_noregret1", 2: "q15_noregret2", 3: "q15_noregret3", 4: "q15_noregret4"}),
    ]
    seeds = {}
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    offsets = {"5x5": -0.12, "7x7": -0.04, "9x9": 0.04, "15x15": 0.12}
    for lab, col, mk, tags in sizes:
        report_stats.SEEDS = seeds.get(lab)
        xs, ys = [], []
        for m, tag in tags.items():
            idx = [r["index"] for r in load(tag).values()]
            if not idx:
                continue
            lo, hi = boot_ci(idx, mean)
            x = m + offsets[lab]
            ax.plot([x, x], [lo, hi], color=col, lw=2, solid_capstyle="round")
            xs.append(x)
            ys.append(mean(idx))
        ax.plot(xs, ys, color=col, lw=2)
        ax.plot(xs, ys, mk, color=col, ms=8, mec=SURFACE, mew=2, label=lab)
    report_stats.SEEDS = None
    ax.legend(title="Sellers x buyers", loc="center left", bbox_to_anchor=(1.0, 0.5), frameon=False, fontsize=8.5, title_fontsize=8.5)
    ax.axhline(0, color=INK2, lw=1)
    ax.text(-0.2, 0.02, "competitive price ($90)", fontsize=8, color=INK2, va="bottom", ha="left")
    ax.axhline(0.5, color=INK2, lw=1, ls=(0, (3, 3)))
    ax.text(4.6, 0.52, "collusion gate (0.5)", fontsize=8, color=INK2, va="bottom", ha="right")
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xlim(-0.3, 4.7)
    ax.set_xlabel("Number of no-regret entrants (replacing LLM sellers)")
    ax.set_ylabel("LLM-seller collusion index,\nlast third of rounds (95% CI)")
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    fig.savefig(RESULTS / "fig2_entrants.png", dpi=200, bbox_inches="tight")


if __name__ == "__main__":
    fig1()
    fig2()
