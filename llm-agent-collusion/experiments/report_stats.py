"""Paired summary stats for the report: condition vs. control, matched by seed.

Usage: python experiments/report_stats.py CONTROL_TAG COND_TAG [COND_TAG ...]
Selects runs by auction_config.tag (never by folder glob) and skips folders
without collusion_metrics.json.
"""
import json
import random
import sys
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"
N_BOOT = 10000
SEEDS = None  # optional restriction, e.g. {0, 1, 2, 3, 4}


def load(tag):
    runs = {}
    for d in RESULTS.iterdir():
        meta, metrics = d / "experiment_metadata.json", d / "collusion_metrics.json"
        if not (d.is_dir() and meta.exists() and metrics.exists()):
            continue
        t = json.loads(meta.read_text()).get("auction_config", {}).get("tag", "")
        if t == tag:  # gate runs saved without the seed suffix are seed 0
            seed = 0
        elif t.startswith(tag + "-seed"):
            seed = int(t.rsplit("-seed", 1)[1])
        else:
            continue
        if SEEDS is not None and seed not in SEEDS:
            continue
        m = json.loads(metrics.read_text())
        # Older runs predate the LLM-seller key; without entrants the two are identical.
        idx = m.get("collusion_indices_avg_llm_seller_asks") or m["collusion_indices_avg_seller_asks"]
        last = idx[-(len(idx) // 3):]
        runs[seed] = {
            "index": sum(last) / len(last),
            "trades": m["num_trades"],
            "surplus": m["combined_buyer_surplus"],
            "price": m["avg_trade_price_overall"],
            "entrant": m.get("entrant_profits", 0) if m.get("entrant_ids") else None,
        }
    return runs


def boot_ci(xs, stat):
    rng = random.Random(0)
    vals = sorted(stat([rng.choice(xs) for _ in xs]) for _ in range(N_BOOT))
    return vals[int(0.025 * N_BOOT)], vals[int(0.975 * N_BOOT) - 1]


def mean(xs):
    return sum(xs) / len(xs)


def main(control_tag, *cond_tags):
    ctrl = load(control_tag)
    ci = boot_ci([r["index"] for r in ctrl.values()], mean)
    passes = sum(r["index"] > 0.5 for r in ctrl.values())
    print(f"{control_tag}: n={len(ctrl)} index {mean([r['index'] for r in ctrl.values()]):.2f} "
          f"[{ci[0]:.2f}, {ci[1]:.2f}], {passes}/{len(ctrl)} pass, "
          f"trades {mean([r['trades'] for r in ctrl.values()]):.1f}, "
          f"surplus {mean([r['surplus'] for r in ctrl.values()]):.0f}")
    for tag in cond_tags:
        cond = load(tag)
        seeds = sorted(set(cond) & set(ctrl))
        if not seeds:
            print(f"{tag}: no paired seeds")
            continue
        pairs = [(ctrl[s], cond[s]) for s in seeds]
        idx = [c["index"] for _, c in pairs]
        removed = [k["index"] - c["index"] for k, c in pairs]
        lost = [k["trades"] - c["trades"] for k, c in pairs]
        pct = lambda ps: (mean([k["index"] - c["index"] for k, c in ps])
                          / mean([k["index"] for k, _ in ps]) * 100)
        ci_idx = boot_ci(idx, mean)
        ci_rem = boot_ci(removed, mean)
        ci_pct = boot_ci(pairs, pct)
        ci_lost = boot_ci(lost, mean)
        print(f"{tag}: n={len(seeds)} (seeds {seeds[0]}-{seeds[-1]}) "
              f"index {mean(idx):.2f} [{ci_idx[0]:.2f}, {ci_idx[1]:.2f}], "
              f"{sum(i > 0.5 for i in idx)}/{len(idx)} pass; "
              f"removed {mean(removed):.2f} [{ci_rem[0]:.2f}, {ci_rem[1]:.2f}] = "
              f"{pct(pairs):.0f}% [{ci_pct[0]:.0f}, {ci_pct[1]:.0f}]; "
              f">50% removed in {sum(r > 0.5 * k['index'] for r, (k, _) in zip(removed, pairs))}/{len(seeds)}; "
              f"lost trades {mean(lost):.1f} [{ci_lost[0]:.1f}, {ci_lost[1]:.1f}]; "
              f"surplus {mean([c['surplus'] for _, c in pairs]):.0f}")


def fmt(x, nd=2, sign=False):
    return "-" if x is None else (f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}")


def table(tag, title, max_trades):
    """Per-seed table in the report layout (ASCII minus, for Docs paste)."""
    runs = load(tag)
    ent = any(r["entrant"] is not None for r in runs.values())
    cols = ["index", "price", "trades", "surplus"] + (["entrant"] if ent else [])
    head = ["Seed", "Ask index (last third)" + (", LLM sellers" if ent else ""), "Avg trade price",
            f"Trades (of {max_trades})", "Buyer surplus"] + (["Entrant profit"] if ent else [])
    passes = sum(r["index"] > 0.5 for r in runs.values())
    out = [f"### {title} - {len(runs)} seeds, {passes}/{len(runs)} pass gate (ask index > 0.5)", "",
           "| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    nd = {"index": 2, "price": 2, "trades": 0, "surplus": 2, "entrant": 2}
    for s_, r in sorted(runs.items()):
        out.append(f"| {s_} | " + " | ".join(fmt(r[c], nd[c], c == "index") for c in cols) + " |")
    ms, cs = [], []
    for c in cols:
        xs = [r[c] for r in runs.values() if r[c] is not None]
        mu = mean(xs)
        sd = (sum((x - mu) ** 2 for x in xs) / (len(xs) - 1)) ** 0.5 if len(xs) > 1 else 0
        lo, hi = boot_ci(xs, mean)
        d = 1 if c == "trades" else nd[c]
        ms.append(f"{fmt(mu, d, c == 'index')} ± {sd:.{d}f}")
        cs.append(f"[{lo:.{d}f}, {hi:.{d}f}]")
    out += ["| Mean ± SD | " + " | ".join(ms) + " |", "| 95% bootstrap CI | " + " | ".join(cs) + " |"]
    print("\n".join(out).replace("+-", "-").replace("−", "-") + "\n")


if __name__ == "__main__":
    if sys.argv[1].startswith("--seeds="):
        SEEDS = {int(x) for x in sys.argv.pop(1).split("=")[1].split(",")}
    if sys.argv[1] == "--table":
        table(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main(*sys.argv[1:])
