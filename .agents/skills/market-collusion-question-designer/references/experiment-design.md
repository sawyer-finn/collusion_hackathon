# Experiment design for market-collusion questions

Use this guide to turn an interesting mechanism into a credible sprint-sized study.

## 1. State the estimand

A research question should imply a quantity that could be estimated. Useful forms include:

- the average treatment effect of restriction \(R\) on a predeclared market-harm metric;
- the change in action dependence caused by \(R\), conditional on economics being held fixed;
- time to collapse or recover a high-price convention after an intervention;
- the minimum restriction intensity that achieves a target reduction;
- the Pareto frontier between reduced collusion and protected legitimate performance.

Avoid treating a bundle such as "oversight enabled" as one mechanism if it simultaneously changes agent instructions, sampling, enforcement, and access to communication.

## 2. Choose an operational definition

Pick one definition family and say what the experiment cannot establish.

### Outcome-based

Collusion is operationalized as persistent performance above a competitive benchmark or closer to a joint-profit benchmark. This is easy to measure but can confuse coordination with market structure, asymmetric technology, poor exploration, or shared priors.

### Strategy-based

Collusion is sustained by reward/punishment or a failure to best-respond after a deviation. This is closer to the economics tradition. It requires a deviation or impulse-response test and may miss threat-free or coupling-based mechanisms.

### Coalition/harm-based

A subset coordinates in a way that improves coalition reward while harming outsiders or the system objective. This travels beyond pricing markets but needs a credible no-coalition counterfactual.

### Dependence-based

Agents' joint actions contain dependence not explained by individual marginals, common observations, or shared priors. This can detect coordination hidden behind competitive-looking individual behavior, but dependence is not by itself intent or illegality.

For a short Track 1 experiment, combine an outcome measure with either a deviation response, an action-dependence measure, or a controlled removal of the alleged coordination channel.

## 3. Build a measurement stack

Predeclare one primary measure. Treat the rest as secondary or diagnostic.

### Market harm

- normalized price/markup relative to competitive and joint-profit benchmarks;
- seller profit and buyer surplus;
- quantity/trade frequency;
- allocative efficiency;
- convergence and persistence, not just a final-round snapshot.

### Coordination

- intervention on the communication or observation channel;
- seller-action dispersion and lagged response to rivals;
- response to a unilateral deviation;
- time to recover a convention after replacement or memory reset;
- action dependence or conditional mutual information;
- transcript judge scores, used as supporting evidence rather than sole ground truth.

### Cost

Report costs in natural units before combining them:

- monitor/model calls and latency;
- messages inspected, characters removed, or agent-rounds restricted;
- sellers gagged, replaced, reset, or sanctioned;
- change in benign-control buyer welfare, seller profit, volume, and efficiency;
- false-positive interventions on non-collusive runs;
- engineering complexity and model-provider dependence.

A restriction is not "cheap" merely because it reduces token use.

## 4. Controls and causal structure

Minimum control set:

- **Positive control:** the chosen model/harness reliably produces the target behavior before scale-up.
- **Negative control:** a condition with common incentives or correlated model priors but no privileged coordination channel.
- **Mechanism control:** remove or alter the proposed pathway while holding the economics fixed.
- **Benign-performance control:** apply the restriction where collusion is absent to measure collateral damage.

Use matched seeds. When a harness supports checkpoint branching, branch multiple treatments from the same pre-intervention history. This removes variation in whether collusion formed and makes post-intervention recovery directly comparable.

If selecting a target agent from baseline behavior, select it using a pre-treatment period or separate pilot data. Do not choose the "leader" after seeing treatment outcomes.

## 5. Positive-control gate

Run in this order:

1. wiring smoke test;
2. one short positive and negative control;
3. enough seeds to estimate whether the effect is stable;
4. only then the treatment comparison.

Set a stopping rule before spending:

- stop or change model if the positive control fails in a predeclared number of seeds;
- stop a detector project if planted coordination is not ranked above controls;
- stop expanding models if the core causal contrast is unresolved in the first model.

An explicit-collusion prompt or pressure condition can be an engineering positive control. Do not silently generalize its result to spontaneous collusion.

## 6. Track 1.5 comparisons

For each intervention \(R\), estimate a vector rather than only one score:

\[
(\Delta \text{market harm},\ \Delta \text{coordination evidence},\
\Delta \text{legitimate performance},\ \text{operational cost})
\]

Call one intervention better only when it dominates another on the declared dimensions. Otherwise show the Pareto tradeoff. If a single ranking is required, publish the weighting rule before results.

Useful cost-normalized quantities include:

- buyer-welfare gained per monitored message;
- reduction in normalized markup per restricted seller-round;
- reduction in dependence per monitor call;
- probability of convention collapse per replaced or reset participant.

Check for non-monotonicity. More monitoring, tighter caps, more noise, or a lower price ceiling can create new focal points or shift coordination into actions.

## 7. Analysis suitable for a sprint

Prefer effect sizes and uncertainty over a crowded collection of significance tests:

- show per-seed trajectories and paired differences;
- use a bootstrap or randomization interval over seeds when appropriate;
- report all attempted positive-control seeds;
- distinguish exploratory metrics from predeclared metrics;
- keep model and prompt fixed for the core result, then use one robustness model if budget remains.

The unit of analysis is usually the run or checkpoint branch, not every round treated as an independent sample.

## 8. Question-quality checklist

A high-quality question can be completed as:

> In [market and agent population], does [single intervention or factorial component]
> change [primary outcome] through [proposed mechanism], compared with [matched control],
> at what [legitimate-performance/operational] cost?

Before recommending it, be able to answer:

- What result would falsify the mechanism?
- What is the closest paper and what is new here?
- What is held fixed?
- What proves the manipulation worked?
- What does a null result teach?
- What is the cheapest decisive version?
