---
name: market-collusion-question-designer
description: Propose, refine, and rank falsifiable research questions about AI-agent collusion in markets, especially Apart Research Sprint Track 1 and subtrack 1.5. Use when choosing a sprint project, checking novelty against nearby work, or turning an idea into a tractable experiment; do not use merely to run an already-specified experiment.
---

# Market Collusion Question Designer

Design the smallest experiment whose result would change a reasonable reader's belief about market collusion. Optimize for scientific information gained within the team's actual time, inference, and engineering budget.

## Ground the proposal

Find the repository root containing `literature/papers.csv`. Then:

1. Read the current sprint Track 1 questions and practical starts. If the page is unavailable, use the snapshot in [references/track-1-landscape.md](references/track-1-landscape.md) and state its date.
2. Read `literature/README.md`, the relevant rows of `literature/papers.csv`, and the README for any proposed harness.
3. Use `scripts/scan_literature.py` to retrieve nearby work. Example:

   ```bash
   python3 .agents/skills/market-collusion-question-designer/scripts/scan_literature.py \
     --project 1.5 --query "overseer message welfare" --limit 20
   ```

4. If web research is available, search primary papers for the proposed mechanism and any work newer than the local literature cutoff. Date-stamp the search. Never call a question "novel" from title/abstract search alone; say "I found no direct test in the sources searched" and name the nearest work.

For Track 1 work, read:

- [references/track-1-landscape.md](references/track-1-landscape.md) for the sprint map, intervention taxonomy, testbeds, and promising gaps.
- [references/experiment-design.md](references/experiment-design.md) before ranking or recommending a question.

## Formulate the scientific object

Before generating candidates, pin down:

- the subtrack and decision the result informs;
- the market, agent population, communication/observation structure, and time horizon;
- an operational definition of collusion;
- the primary causal contrast;
- the team's time, API budget, available models, and tolerance for harness changes.

Distinguish these outcomes:

- **Anticompetitive outcome:** prices, markups, seller profit, buyer surplus, quantity, or allocative efficiency.
- **Coordination evidence:** communication, action dependence, response to deviations, coalition advantage, or recovery of a convention.
- **Intervention cost:** lost legitimate performance, monitor calls, restricted agent-rounds, latency, false-positive sanctions, and engineering/API cost.

High prices alone do not establish coordination. Collusive language alone does not establish market harm. A strong question measures at least one market outcome and one coordination-sensitive signal, or explicitly says it studies only one of them.

## Generate candidates

Prefer questions with one interpretable causal contrast. Productive gap types include:

- unbundling a published intervention into its active components;
- targeting one participant instead of restricting everyone;
- changing when an intervention is applied, especially after collusion forms;
- transferring an intervention across market formats or agent architectures;
- testing a backfire mechanism, such as a restriction becoming a focal point;
- comparing an outcome-only detector with a dependence-sensitive measure;
- finding the minimum intervention intensity that crosses a predeclared effect threshold.

For subtrack 1.5, do not ask "which restriction is best?" until the candidate set, baseline, cost units, and protected legitimate behavior are specified. Prefer a Pareto comparison of collusion reduction and cost over a brittle single weighted score.

## Stress-test each candidate

Reject or revise a candidate if any of these fail:

- There is no reliable positive control in the chosen model and harness.
- The main contrast changes several economically meaningful variables at once.
- The proposed evidence cannot distinguish coordination from common incentives or shared model priors.
- "Cost" means only API spend while ignoring buyer welfare, trade volume, or restrictions on benign agents.
- The experiment needs a large model-by-market grid before yielding any interpretable result.
- A null result would be uninterpretable because the manipulation, detector, or collusive baseline was not validated.
- The claim is already the central result of the nearest paper, rather than a discriminating extension.

Use matched seeds or checkpoint branches when available. Freeze the primary metric, thresholds, exclusions, and monitor prompt before examining treatment results.

## Rank and report

Score each candidate from 1–5 on:

- sprint relevance;
- novelty relative to named nearest work;
- causal clarity;
- measurement validity;
- positive-control reliability;
- weekend feasibility;
- value of either a positive or null result.

Treat missing ground truth, an unreliable positive control, or infeasible call count as vetoes rather than small score deductions.

Return:

1. A short recommendation naming the best question and why it dominates the alternatives.
2. Three to six ranked **question cards**, each with:
   - one-sentence question and subtrack;
   - nearest prior work and the exact delta;
   - main hypothesis and strongest competing explanation;
   - experimental unit, arms, controls, and positive-control gate;
   - primary market outcome, coordination evidence, and cost measure;
   - estimated calls, engineering risk, and a stopping rule;
   - what a positive result, null result, and failed positive control would mean;
   - score breakdown and confidence in the novelty assessment.
3. A minimal first-day plan for the top choice: preflight, cheapest smoke test, and the decision gate before scaling.
4. A short "do not claim" section separating demonstrated findings from speculative mechanisms.

When the user's constraints are missing, make conservative weekend assumptions and label them instead of blocking.
