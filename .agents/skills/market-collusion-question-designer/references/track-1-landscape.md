# Track 1 market-collusion landscape

Snapshot: 2026-10-24. Refresh against the sprint page and primary literature when possible.

## Sprint questions and local testbeds

| Subtrack | Sprint question | Best local starting point |
|---|---|---|
| 1.1 | Which variables are necessary for collusion to emerge? | `algorithmic-pricing-llms/`, `llm-cartel/` |
| 1.2 | Is formed collusion robust to replacing participants? | `llm-cartel/branch_game.py`, `focal-points/` |
| 1.3 | Can detection improve, including without communication? | `llm-agent-collusion/`, `focal-points/` |
| 1.4 | Can information-theoretic methods identify colluding pairs? | Implement on a scripted game, then use `llm-agent-collusion/` |
| 1.5 | Which single restriction removes the most collusion at the least cost? | `llm-agent-collusion/` |

The 1.5 practical start uses a 3-seller, 3-buyer, 15-round continuous double auction and suggests comparing no seller messages, a short message cap, an oversight condition, and temperature while tracking prices/profit plus trade volume/buyer welfare. Scale only after a collusive positive control works.

## What nearby work already covers

Do not present these broad claims as new:

- Prompt wording and market framing can change LLM pricing outcomes: [Fish et al. 2024](https://arxiv.org/abs/2404.00806).
- Seller communication, message restrictions, oversight, pressure, and model mix have been manipulated in an LLM double auction: [Agrawal et al. 2025](https://arxiv.org/abs/2507.01413).
- Adding firms, mixing LLM families, or adding a non-LLM learner can weaken or collapse pricing collusion: [Keppo et al. 2026](https://arxiv.org/abs/2603.20281).
- A single no-regret participant can disrupt high-price outcomes in mixed human/algorithm markets: [Collina et al. 2025](https://arxiv.org/abs/2511.21935).
- Public governance instructions have produced small, heterogeneous reductions in LLM Cournot collusion: [Bracale Syrnikov et al. 2026](https://arxiv.org/abs/2601.11369).
- Prompt warnings and a strategy-targeting rule have been tested in an LLM Bertrand setting: [Garra 2026](https://arxiv.org/abs/2609.13037).
- Partner persistence, price visibility, and messaging affect learned-agent prices in a preregistered pricing experiment: [Arslan et al. 2026](https://arxiv.org/abs/2609.35402).
- Newcomers and heterogeneous buyers can destabilize heterogeneous-LLM collusion: [Lee 2026](https://arxiv.org/abs/2610.11256).
- Auction format and feedback disclosure can determine whether learning bidders suppress bids: [Banchio & Skrzypacz 2022](https://arxiv.org/abs/2202.05947).
- A deterministic price cap can become a focal point for LLM pricing agents: [Dhanda 2026](https://doi.org/10.21203/rs.3.rs-10183486/v1).
- Price-level audits can miss joint dependence when each agent's marginal behavior looks competitive: [Xu et al. 2026](https://arxiv.org/abs/2607.26385).
- External-regret guarantees do not rule out collusion; stronger domination-avoiding properties can: [Nisan et al. 2026](https://arxiv.org/abs/2606.01275).

These results leave many mechanism-level and cost-comparison questions open. The safe novelty move is usually to isolate a component, target a subset of agents, use a matched checkpoint, or test whether apparent compliance transfers from language to actions and welfare.

## Intervention taxonomy

| Lever | Examples | Main confound or failure mode | Useful unexplored delta |
|---|---|---|---|
| Communication | remove chat, character cap, paraphrase, rate limit | coordination can move into prices/timing; caps can compress a code | target one seller; randomize semantics; measure action dependence |
| Observation/feedback | hide exact rival prices, delay history, bin/noise feedback | less information can also reduce legitimate competition | compare coarse/delayed feedback with a no-chat restriction at matched welfare cost |
| Memory/history | shorten window, reset notes, erase one seller's history | may merely delay rather than break a convention | branch after collusion and measure collapse/recovery time |
| Identity/persistence | rotate names, partners, providers, or model families | changing capability along with identity | separate pseudonym rotation, history reset, and actual model replacement |
| Population | add a competitive, no-regret, Q-learning, or heterogeneous agent | entrant may change market capacity or competence | restrict only one participant; compare targeted vs market-wide cost |
| Instructions/governance | anti-collusion prompt, monitoring notice, public rule graph | agents may learn to avoid suspicious language without changing actions | separate warning, inspection, and enforcement |
| Randomness | temperature, stochastic intervention timing, noisy observations | worsens decision quality and may create volatility | perturb one agent or use minimal intensity; measure benign-control damage |
| Incentives/sanctions | deposits, fines, leniency, whistleblower reward | described penalties may be prompt salience rather than learned utility | vary expected penalty and salience independently |
| Market design | cap, reserve price, feedback disclosure, demand steering | policy can create a new focal point or redistribute welfare | deterministic vs jittered/agent-specific rule |
| Monitoring | full, sampled, triggered, or silent oversight | monitor errors and calls are costly; monitored text is not behavior | compare constant with threshold-triggered monitoring per inspected message |

## Priority opportunities

These are hypotheses and design templates, not claims that no paper has tested them. Refresh the nearest-work search before use.

### 1. Decompose oversight into warning, inspection, and enforcement

**Question:** In a communication-enabled LLM double auction, is the apparent anti-collusion effect of oversight caused by telling sellers they are watched, actually inspecting messages, or enforcing a consequence—and which component improves buyer welfare per monitor call?

Why it is strong:

- The local Agrawal harness bundles an overseer with an enforcement response.
- A 2×2 or staged design isolates deterrence from enforcement.
- It catches the important failure mode where suspicious language falls while prices and action dependence do not.
- Cost has natural units: monitor calls, messages inspected, and seller-rounds gagged.

Minimal arms:

1. no warning, no enforcement;
2. warning only;
3. silent inspection/enforcement;
4. warning plus inspection/enforcement.

Hold seller communication, economics, model, prompt, temperature, rounds, and matched seeds fixed. Primary outcome: buyer surplus or normalized seller ask. Secondary: trade volume, action dependence, transcript score. Add a benign no-communication control to estimate collateral intervention.

Engineering risk: low-to-medium; decouple the prompt notice and overseer action flags.

### 2. Restrict one seller rather than the whole market

**Question:** Is restricting one randomly preselected seller's messaging enough to destabilize coordinated pricing, and how much of a market-wide restriction's welfare benefit does it recover per restricted seller-round?

Why it is strong:

- It tests the "single breaker" intuition without requiring a new learning algorithm.
- The direct comparison is targeted versus universal intervention, not merely restriction versus none.
- It yields a clear cost denominator.

Arms: unrestricted communication; one seller capped or muted; all sellers capped or muted. Preselect the target independently of treatment results. If a leadership-based target is explored, choose it from a separate pilot or pre-intervention period.

Engineering risk: medium; add per-seller communication controls.

### 3. Reset visible history after collusion forms

**Question:** After a high-price convention forms, does erasing one seller's visible history break it as effectively as replacing that seller with a different model, with less disruption to legitimate market performance?

Why it is strong:

- It joins 1.2's replacement question to 1.5's intervention-cost question.
- `llm-cartel/branch_game.py` already supports checkpoint branches and a replacement with a zero history window.
- Each treatment can branch from the identical collusive history.

Arms: no change; same model with zero visible history; different model with preserved history; different model with zero history. Measure price/gain collapse, time to recover, total welfare, and calls/participants changed.

Engineering risk: low; verify that "same model, zero history" is implemented as the intended branch.

### 4. Coarsen or delay rival-price feedback

**Question:** Does replacing exact rival-price history with binned or delayed feedback reduce LLM coordination at a lower buyer-welfare cost than removing seller chat?

Why it is strong:

- It transfers a classic information-design lever into an LLM-agent setting.
- It tests whether exact observability is the stabilizing channel even without explicit messages.
- It can produce a useful backfire result if less feedback impedes competitive undercutting.

Engineering risk: medium; change prompt-visible history while keeping the market state exact.

### 5. Randomize a price cap to avoid focal-point coordination

**Question:** Do deterministic caps coordinate LLM sellers on the ceiling, while small per-run or per-seller cap jitter preserves the consumer-protection benefit without increasing joint action dependence?

Why it is strong:

- It directly follows a documented backfire mechanism.
- The treatment targets focal salience, not just cap level.
- Dependence-sensitive evidence avoids calling any lower price "less collusive."

Engineering risk: medium. Predeclare cap distributions and ensure the randomized rule does not create unfair capacity differences.

### 6. Separate expected penalty from sanction wording

**Question:** Do LLM sellers respond to the expected economic cost of a collusion penalty, or mainly to the salience and wording of the warning?

Use a factorial design that varies probability × penalty size while separately varying warning strength. This is scientifically attractive but riskier for a weekend because API-driven LLM agents do not learn utility from repeated reward in the same way as online learners.

Engineering risk: medium-to-high. Treat it as a prompt-and-decision study unless the agent policy actually updates from realized payoffs.

## Lower-priority weekend ideas

- An exhaustive comparison across many restrictions, models, temperatures, and markets: too many interactions before a core result.
- Building a no-regret or domination-avoiding agent from scratch before establishing the LLM positive control.
- Calling lower prices "less collusion" without coordination-sensitive evidence.
- Using an LLM transcript judge as the only target metric.
- Evaluating a detector only on naturally occurring trajectories with no planted or channel-ablation ground truth.
- Comparing different providers while simultaneously changing prompt templates, inference settings, and market roles.

## Local evidence worth exploiting

The bundled `llm-agent-collusion/data/` contains 75 published runs with messages, asks, trades, welfare metrics, and judge outputs across communication, oversight, pressure, and model-mix conditions. Use it to:

- estimate metric variance before buying new runs;
- find whether oversight changes language more than asks or welfare;
- choose plausible effect thresholds;
- identify a positive-control configuration;
- test analysis code without API calls.

Do not treat the stored runs as randomized evidence for a new factorial comparison when the cells changed several factors or model roles.

Audit the metrics before reusing them:

- `evaluation/metrics.py::gini` appears to multiply by total value where the standard formula divides by it; stored Gini values should not be used without correction and recomputation.
- `collusion_auc` substitutes zero when a round has no valid bid. In a market with many no-trade rounds, this can make a trade-price index look competitive while seller asks remain high. Prefer the ask-based index alongside trade frequency and welfare, and state how missing prices are handled.
- Treat a run or checkpoint branch as the sampling unit. Rounds within a run are serially dependent and should not be counted as independent replicates.
