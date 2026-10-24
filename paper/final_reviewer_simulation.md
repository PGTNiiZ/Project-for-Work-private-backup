# Anonymous Reviewer Simulation and Revision Record

## Reviewer 1 — Evolutionary Computing

Scores (1–5): Novelty 3; Technical Quality 4; Experimental Rigor 4; Reproducibility 4; Clarity 4; Related Work 3; Significance 3; Overall 3 (Weak Accept).

Major concerns:

1. The GA is a conventional four-gene threshold policy; novelty cannot be the optimizer itself.
2. A scalar utility based on unmeasured coefficients may appear arbitrary.
3. The paper should show that GA gains are not one-split artifacts.

Required revision:

- Present the contribution as operational-policy evaluation, not a new GA.
- Put the three per-outer-split F1 outcomes in the main results table.
- State that the utility is illustrative and show its sensitivity limitation.

## Reviewer 2 — Machine Learning / Entity Resolution

Scores (1–5): Novelty 3; Technical Quality 4; Experimental Rigor 4; Reproducibility 4; Clarity 4; Related Work 4; Significance 3; Overall 3 (Weak Accept).

Major concerns:

1. The MiniLM ablation is mixed across outer splits and must not be characterized as consistently beneficial.
2. Candidate recall limits end-to-end results, so pair-model and workflow claims must remain separate.
3. LinkSocial provenance/license constraints require an explicit restricted-data statement.

Required revision:

- Report the mixed GB-17 versus GB-18 repeated-split outcome in the abstract/discussion.
- Give candidate recall and misses a dedicated result paragraph.
- Add a data availability and ethics statement.

## Reviewer 3 — Experimental Methodology

Scores (1–5): Novelty 3; Technical Quality 4; Experimental Rigor 4; Reproducibility 4; Clarity 4; Related Work 3; Significance 3; Overall 3 (Weak Accept).

Major concerns:

1. Three outer partitions improve evidence but are not external validation.
2. The primary bootstrap is conditional on one test candidate population and fixed retrieval constants.
3. The repeated study needs clear test-isolation and per-split reporting.

Required revision:

- Add the per-split F1 results and outer-split count.
- State test-label isolation and bootstrap scope explicitly in Results and Limitations.
- Avoid significance language and generalization claims.

## Revision applied

The revised manuscript:

- explicitly labels novelty as an empirical operational composition;
- adds per-split F1 values to the main table;
- marks MiniLM results as mixed across repeated splits;
- gives RQ3 a dedicated retrieval-ceiling result;
- describes utility as illustrative and scenario-specific;
- adds an explicit restricted-data/ethics paragraph;
- states that repeated splits are within-corpus evidence and that conditional bootstrap intervals are not population-level inference.

## Residual decision

The reviewers support a narrowly framed paper but would reject claims of new GA/three-way linkage, real business cost, external generalization, or unrestricted data reproducibility.
