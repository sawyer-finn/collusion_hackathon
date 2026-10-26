"""Every number quoted in the report text that is not in a report_stats.py table.

Reads only run logs in results/ (unified.log, collusion_metrics.json, experiment_metadata.json,
and seller transcripts where present). Runs are selected by auction_config.tag, never by folder name.

Usage: python3 experiments/report_text_numbers.py
"""
import glob
import json
import random
import re
import statistics as st
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results"

# Keyword coding used in Table G5 (documented in its caption).
NAME_PRICE = re.compile(r"\$\s?\d|\b(8\d|9\d)(\.\d+)?\b")
IN_90S = re.compile(r"\b9\d(\.\d+)?\b")
UNDERCUT = re.compile(r"undercut|price war|race to the bottom", re.I)
INDEP = re.compile(r"independen", re.I)
COMPLY = re.compile(r"complian|regulat|oversight|scrutiny|ethical", re.I)


def runs(tag, seeds=None):
    out = {}
    for meta in RESULTS.glob("*/experiment_metadata.json"):
        t = json.loads(meta.read_text()).get("auction_config", {}).get("tag", "")
        if t == tag:
            seed = 0
        elif t.startswith(tag + "-seed"):
            seed = int(t.rsplit("-seed", 1)[1])
        else:
            continue
        if seeds is None or seed in seeds:
            out[seed] = meta.parent
    return dict(sorted(out.items()))


def rounds(d):
    res = []
    for line in open(d / "unified.log"):
        if "completed with result: " in line:
            res.append(json.loads(line.split("completed with result: ", 1)[1]))
    return res


def llm_asks(r, d):
    meta = json.loads((d / "experiment_metadata.json").read_text())
    ent = set(meta.get("entrant_ids") or [])
    return {k: v for k, v in r["seller_asks"].items() if k not in ent and v is not None}


def mean(xs):
    return sum(xs) / len(xs)


def boot(xs, n=10000):
    rng = random.Random(0)
    v = sorted(mean([rng.choice(xs) for _ in xs]) for _ in range(n))
    return v[int(0.025 * n)], v[int(0.975 * n) - 1]


def msgs(dirs):
    return [m for d in dirs for r in rounds(d) for m in r["seller_messages"].values() if m]


def share(ms, rx):
    return 100 * sum(bool(rx.search(m)) for m in ms) / len(ms)


def ask_spread(dirs):
    """Std of the LLM sellers' asks in each of rounds 11-15, averaged over rounds and runs."""
    out = []
    for d in dirs:
        for r in rounds(d)[10:15]:
            a = list(llm_asks(r, d).values())
            if len(a) > 1:
                out.append(st.pstdev(a))
    return mean(out)


def section(t):
    print(f"\n== {t}")


S5 = range(5)

section("4.1 Baseline (control41)")
c10 = list(runs("control41").values())
c5 = list(runs("control41", S5).values())
print(f"mean trade price, 10 seeds: ${mean([json.loads((d/'collusion_metrics.json').read_text())['avg_trade_price_overall'] for d in c10]):.2f}")
r1 = [mean(list(llm_asks(rounds(d)[0], d).values())) for d in c5]
print(f"round-1 mean ask (seeds 0-4): ${mean(r1):.2f}; round-1 index by seed: "
      + ", ".join(f"{(x-90)/10:.2f}" for x in r1))
m = msgs(c5)
print(f"messages: {len(m)}; name a price in the $90s: {share(m, IN_90S):.0f}%; "
      f"warn against undercutting: {share(m, UNDERCUT):.0f}%")

section("4.2 Message cap: share of messages repeating an earlier message in the same run")
rep = tot = 0
for d in runs("c2_msgcap", S5).values():
    seen = set()
    for r in rounds(d):
        for v in r["seller_messages"].values():
            if not v:
                continue
            k = re.sub(r"[^a-z]", "", v.lower())
            tot += 1
            rep += k in seen
            seen.add(k)
print(f"{rep}/{tot} = {100*rep/tot:.0f}%")

section("Table G5: message coding and ask spread (seeds 0-4)")
G5 = [("No enforcement (enforcement code)", "control_thresh3"), ("Ex-post, threshold 4", "expost_corrected"),
      ("Immediate, threshold 4", "immediate_corrected"), ("Ex-post, threshold 3", "expost_thresh3"),
      ("Immediate, threshold 3", "immediate_thresh3"), ("Ex-post, threshold 2", "expost_thresh2_boss"),
      ("Immediate, threshold 2", "immediate_thresh2_boss"), ("Ex-post, threshold 1", "expost_thresh1_boss"),
      ("Immediate, threshold 1", "immediate_thresh1_boss"), ("Dark book", "dark_book_comms"),
      ("Partial transparency", "partial_transparency_boss"), ("Sequential asks", "sequential_asks_boss")]
print("condition | messages | name price | undercut | independence | compliance | ask spread")
for name, tag in G5:
    ds = list(runs(tag, S5).values())
    m = msgs(ds)
    print(f"{name} | {len(m)} | {share(m, NAME_PRICE):.0f}% | {share(m, UNDERCUT):.0f}% | "
          f"{share(m, INDEP):.0f}% | {share(m, COMPLY):.0f}% | ${ask_spread(ds):.2f}")

section("4.2 Fines actually imposed (immediate, threshold 3; seller transcripts)")
for seed, d in runs("immediate_thresh3", S5).items():
    tot_f = []
    for f in sorted(d.glob("Seller *.md")):
        hits = re.findall(r"fined a total of \$([0-9.,]+)", f.read_text())
        tot_f.append(float(hits[-1].replace(",", "")) if hits else 0.0)
    print(f"seed {seed}: sellers fined {sum(x > 0 for x in tot_f)}/{len(tot_f)}, totals "
          + ", ".join(f"${x:.2f}" for x in tot_f))
late = [(seed, r["round_number"], s, v) for seed, d in runs("immediate_thresh3", S5).items()
        for r in rounds(d) for s, v in r["seller_messages"].items()
        if v and r["round_number"] >= 12 and re.search(r"fin(ed|ing)", v, re.I)]
print(f"seller messages in rounds 12-15 mentioning being fined: {len(late)}")
for x in late[:3]:
    print("  ", x)

section("4.3 Observation-level interventions (seeds 0-4)")
for tag in ["dark_book_comms", "sequential_asks_boss", "partial_transparency_boss"]:
    ds = list(runs(tag, S5).values())
    r1 = [mean(list(llm_asks(rounds(d)[0], d).values())) for d in ds]
    late_ask = [mean([mean(list(llm_asks(r, d).values())) for r in rounds(d)[10:15]]) for d in ds]
    print(f"{tag}: round-1 mean ask ${mean(r1):.2f} (runs ${min(r1):.2f}-{max(r1):.2f}); "
          f"mean ask rounds 11-15 ${mean(late_ask):.2f}")

section("4.4 Second entrant: paired gap, two vs one no-regret entrant (% of control index)")
ctrl = runs("control41")
one, two = runs("c9_noregret1"), runs("c10_noregret2")


def idx(d):
    mm = json.loads((d / "collusion_metrics.json").read_text())
    x = mm.get("collusion_indices_avg_llm_seller_asks") or mm["collusion_indices_avg_seller_asks"]
    last = x[-(len(x) // 3):]
    return mean(last)


seeds = sorted(set(ctrl) & set(one) & set(two))
cm = mean([idx(ctrl[s]) for s in seeds])
gap = [(idx(one[s]) - idx(two[s])) / cm * 100 for s in seeds]
lo, hi = boot(gap)
print(f"n={len(seeds)}: {mean(gap):.0f} points [{lo:.0f}, {hi:.0f}]")

section("4.4 Early sales (rounds 1-5) and lowest early ask, 5x5 and 7x7 runs")
starv = ["control41", "c8_random", "c9_noregret1", "c8b_random2", "c10_noregret2", "c11_mixed",
         "q7_control", "q7_noregret1", "q7_noregret2", "q7_noregret3"]
n = none = held = 0
for tag in starv:
    for d in runs(tag).values():
        meta = json.loads((d / "experiment_metadata.json").read_text())
        ent = set(meta.get("entrant_ids") or [])
        R = rounds(d)
        sold = any(t["seller_id"] not in ent for r in R[:5] for t in r["trades"])
        n += 1
        if not sold:
            none += 1
            held += idx(d) > 0.5
print(f"runs {n}; LLM sellers sold nothing in rounds 1-5: {none}; of these, index > 0.5: {held}")

section("Appendix B: mean over rounds 1-5 of the lowest ask, highest bid and LLM mean ask")
for tag in starv:
    lo_, hb, la = [], [], []
    for d in runs(tag).values():
        R = rounds(d)[:5]
        lo_.append(mean([min(r["seller_asks"].values()) for r in R]))
        hb.append(mean([max(v for v in r["buyer_bids"].values() if v is not None) for r in R]))
        la.append(mean([mean(list(llm_asks(r, d).values())) for r in R]))
    print(f"{tag}: lowest ask {mean(lo_):.2f}, highest bid {mean(hb):.2f}, LLM mean ask {mean(la):.2f}")
