# CRM Cost Model for R3 GA

## Purpose

This document fixes the cost policy used to optimize the R3 decision rule from
operational CRM estimates, rather than from an arbitrary FP/FN ratio.

## Inputs

The following estimates were selected for this project:

| Item | Estimate |
| --- | ---: |
| CRM reviewer labor cost | 100 THB/hour |
| Manual REVIEW time | 1 minute/pair |
| Detect, unmerge, and repair a false merge | 20 minutes/FP |
| Resolve a missed merge after discovery | 10 minutes/FN |

The labor cost per minute is:

$$
c_{minute} = \frac{100}{60} = 1.6667\ \text{THB/minute}
$$

## Event Cost Estimate

Only labor time is included. Reputational loss, incorrect outreach, and lost
revenue are excluded because this project has no observed CRM incident data for
estimating them.

| Event | Formula | Estimated cost |
| --- | --- | ---: |
| False positive (FP) | $20 \times 1.6667$ | 33.33 THB |
| False negative (FN) | $10 \times 1.6667$ | 16.67 THB |
| Manual review (REVIEW) | $1 \times 1.6667$ | 1.67 THB |

Set the FN cost as one normalized cost point:

$$
W_{FP} = \frac{33.33}{16.67} = 2.00,\qquad
W_{FN} = 1.00,\qquad
W_{REV} = \frac{1.67}{16.67} = 0.10
$$

The fixed CRM policy for this run is therefore:

$$
\boxed{\text{Cost}(g) = 2.00\cdot FP + 1.00\cdot FN + 0.10\cdot REVIEW}
$$

## Interpretation

Under the stated operational assumptions, resolving one false merge costs the
same as resolving two missed merges. Reviewing one pair costs one tenth of a
missed merge. These are cost points derived from time estimates, not model
parameters learned from labels.

## Reproducible R3 Run

Run GA using validation data to select the genome. The runner evaluates the
held-out test split only after selection.

```zsh
python3.11 -m experiments.code.run_ga_experiments \
  --experiment r3 \
  --seeds 7 42 123 999 2025 \
  --w-fp 2.0 \
  --w-fn 1.0 \
  --w-review 0.1 \
  --run-id r3_crm_cost_2_1_0p1_20260826
```

The generated `summary.json`, `summary.md`, `trials.csv`, and `generations.csv`
must be retained under `experiments/automation/r3_crm_cost_2_1_0p1_20260826/`.

## Limitation

The inputs are project assumptions supplied for this run. If observed CRM logs
later provide actual repair, review, or missed-match handling times, replace the
four input estimates, recalculate the weights, and run the same command again.