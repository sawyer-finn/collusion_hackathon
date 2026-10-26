# AI Collusion Sprint Track 1: research-question shortlist

Prepared 2026-10-24 for the Apart Research AI Collusion Research Sprint.

## Recommendation

If the team stays with Track 1.5, the best weekend question is:

> In a communication-enabled LLM double auction, is the apparent anti-collusion effect of oversight caused by the warning, by actual inspection and enforcement, or merely by suppressing collusive language—and which component improves buyer welfare per monitor call?

This is stronger than a flat comparison of message caps, temperature, and oversight because it isolates a mechanism inside the supplied harness. It also targets a live measurement problem: agents can sound compliant while their asks and market outcomes remain coordinated.

The closest work is [Agrawal et al. 2025](https://arxiv.org/abs/2507.01413), whose environment exposes communication, oversight, pressure, message length, and temperature. The proposed delta is to unbundle the current oversight condition into:

- warning/no warning;
- overseer enforcement/no enforcement;
- optionally, inspection without enforcement as a cost-only arm.

Do not claim the broad novelty that "oversight of LLM markets has not been tested." Claim the narrower contribution: a causal decomposition of deterrence language versus monitor-backed enforcement, evaluated on both market behavior and transcript evidence.

## Why this direction emerged

The sprint's 1.5 question asks which restriction removes the most collusion at the least cost. The nearby literature already covers many isolated levers:

- message throttling and oversight in double auctions;
- temperature and cross-agent dependence;
- heterogeneous or non-LLM entrants;
- anti-collusion prompts and public governance rules;
- participant replacement and partner persistence;
- deposits or penalties;
- price caps, including evidence that a cap can become a focal point.

The underexplored layer is *what component of an intervention does the work*, whether apparent compliance survives action-based measurement, and how much benign performance it destroys.

## Exploratory signal in the bundled data

The repository contains 75 published double-auction runs. The following aggregates use the 10-run same-model GPT-4.1 cells and are descriptive, not a new randomized result:

| Seller condition | Ask-index AUC | Mean transcript coordination score | Buyer surplus | Trade frequency |
|---|---:|---:|---:|---:|
| No communication | -0.06 | 2.22 | 869 | 0.494 |
| Communication | 5.11 | 3.79 | 593 | 0.348 |
| Communication + oversight | 1.54 | 1.98 | 817 | 0.394 |
| Communication + high-price pressure | 19.13 | 3.88 | 86 | 0.155 |
| Pressure + oversight | 18.92 | 2.29 | 104 | 0.185 |

The most useful hypothesis-generating pattern is the last pair: under pressure, oversight sharply reduces the transcript judge score while the ask index and buyer outcomes barely move. That is consistent with linguistic compliance without behavioral correction, but the stored runs do not isolate the mechanism. A matched factorial study would.

Before reusing metrics, note two implementation issues:

- the current Gini formula appears incorrect and produces impossible stored values;
- the trade-price collusion AUC substitutes zero on missing-bid rounds, so it can disagree with high asks in no-trade markets.

Use normalized seller asks as the primary harm trajectory, plus buyer surplus and trade frequency. Treat transcript scores as secondary evidence.

## Ranked question cards

### 1. Warning versus enforcement in oversight — Track 1.5

**Question.** Does an oversight warning deter LLM seller coordination, or is actual monitor-backed enforcement necessary to improve market outcomes?

**Nearest work and delta.** Agrawal et al. test an oversight bundle. This study separates the warning from the monitor and gag-order response.

**Hypothesis.** Warning-only reduces overt collusive language more than it reduces prices or action dependence. Enforcement produces the larger welfare effect.

**Competing explanation.** Any difference comes from extra prompt salience or monitor noise, not strategic adaptation.

**Core arms.**

1. no warning, no enforcement;
2. warning only;
3. silent inspection plus enforcement;
4. warning plus inspection/enforcement.

Use matched seeds, the same seller communication channel, model, economics, temperature, and initial conditions.

**Measures.**

- Primary: seller-ask collusion-index AUC or late-round normalized asks.
- Coordination: action dependence/dispersion and transcript score.
- Legitimate performance: buyer surplus and trade frequency.
- Cost: monitor calls, messages inspected, and gagged seller-rounds.

**Positive-control gate.** Require a communication-enabled condition to exceed a predeclared ask-index threshold in at least two of three pilot seeds. If it fails, change model or use a clearly labeled high-price-pressure condition only as an elicited mechanism benchmark.

**Pilot size.** Four cells × three seeds × 15 rounds is about 1,080 agent calls plus 90 overseer calls. Avoid full per-seller per-round judge scoring until the market contrast works.

**Score.** Relevance 5, novelty 4, causal clarity 5, validity 5, positive control 4, feasibility 4, null-result value 5: **32/35**.

### 2. Reset one seller's history after collusion — Tracks 1.2/1.5

**Question.** After a high-price convention forms, does erasing one seller's visible history break it as effectively as replacing the seller with a different model, with less market disruption?

**Nearest work and delta.** Replacement fragility is established for learning agents and studied for heterogeneous LLM markets. The local `branch_game.py` enables a matched decomposition of model replacement versus loss of convention history.

**Arms.**

1. no-change branch;
2. same model, zero visible pre-branch history;
3. different model, history preserved;
4. different model, zero history.

**Measures.** Price/gain drop, rounds to recover, seller profit, and the number of participants or histories modified.

**Pilot size.** Ten collusive base runs are unnecessary at first. Find three passing bases, create four 50-round branches from each, and analyze paired post-branch differences.

**Score.** 32/35. This is the lowest-engineering-risk alternative, but it is less purely 1.5 than the oversight question.

### 3. Restrict only one seller — Track 1.5

**Question.** Is muting or tightly capping one preselected seller enough to recover most of a market-wide communication ban's welfare benefit per restricted seller-round?

**Nearest work and delta.** A single no-regret or heterogeneous participant can destabilize collusion, while message restrictions have been applied market-wide. The delta is a targeted LLM communication restriction with a natural cost comparison.

**Arms.** Unrestricted; one randomly preselected seller restricted; all sellers restricted.

**Main risk.** Per-agent communication controls require a harness change, and arbitrary target selection may conceal a leader-specific effect. Leadership targeting belongs in a follow-up using pre-treatment selection.

**Score.** 31/35.

### 4. Coarse or delayed rival-price feedback — Tracks 1.1/1.5

**Question.** Does replacing exact rival-price history with binned or delayed feedback reduce LLM coordination at lower welfare cost than removing seller chat?

**Nearest work and delta.** Feedback disclosure and noisy observations matter for learning agents; the direct transfer to an LLM double auction is less developed.

**Mechanism test.** Hold the true market state fixed and alter only what sellers see. Compare no chat/exact prices, chat/exact prices, and chat/coarse or delayed prices.

**Main risk.** Less information can impede legitimate undercutting and increase prices. That backfire would still be informative if buyer welfare and action dependence are measured.

**Score.** 29/35.

### 5. Deterministic versus jittered price caps — Track 1.5

**Question.** Does small cap randomization prevent a price ceiling from becoming a coordination focal point while preserving its consumer-protection benefit?

**Nearest work and delta.** A deterministic LLM price cap has already been shown to act as a focal point. The delta is testing whether predictable common salience, rather than merely the ceiling level, drives the effect.

**Measures.** Prices relative to the cap, bunching at the ceiling, joint action dependence, quantity, and buyer welfare.

**Main risk.** Per-seller caps change competitive symmetry; prefer per-run public jitter first, then study asymmetric caps separately.

**Score.** 27/35.

## First-day plan for the top question

1. Reanalyze the stored 75 runs and reproduce the descriptive table above from source files.
2. Confirm the positive-control cell with the exact model/provider available to the team.
3. Split `oversight_enabled` into two independent concepts: a seller-visible warning and monitor-backed enforcement.
4. Run four one-seed, five-round wiring tests.
5. Freeze the primary ask metric, buyer-welfare secondary metric, and positive-control threshold.
6. Run three seeds per arm at 15 rounds.
7. Scale to five seeds or 30 rounds only if the positive control works and the main contrast is not dominated by run-to-run noise.

## Do not claim

- Do not equate high prices with proven agreement or intent.
- Do not equate lower transcript scores with reduced collusion.
- Do not call an intervention "least cost" without reporting market-performance and operational costs.
- Do not generalize from a high-price-pressure positive control to spontaneous collusion.
- Do not claim a universal best restriction from one model and one market.
- Do not treat rounds within a run as independent samples.
