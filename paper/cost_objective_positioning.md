# Cost-Objective Positioning

## Options evaluated

### Option A — empirical or stakeholder cost justification

Not supported. The repository has no measured review time, false-merge remediation cost, stakeholder elicitation record, or cited economic model. This option must not be used.

### Option B — illustrative operational utility scenario

Supported. The implemented GA already uses an explicit objective, and the paper can transparently describe it as a declared scenario-specific utility:

`U = 2·FP + 1·FN + 0.1·REVIEW`.

Recommended wording: “We use an illustrative operational utility scenario that penalizes false-positive matches twice as heavily as missed matches and assigns a smaller review burden. These coefficients are design assumptions rather than measured economic costs.”

### Option C — multi-objective / Pareto-style reporting

Partially supported. The paper already reports FP, FN, review count, precision, recall, and F1. These must appear beside utility, but the implemented GA is scalar-objective rather than a Pareto optimizer. Claiming a multi-objective method would be inaccurate.

## Recommendation

Use Option B with Option C-style transparent reporting. Optimize the declared utility, but present all component outcomes and sensitivity results so readers can apply alternative operational preferences.

## Sensitivity adequacy

The existing 12-scenario frozen-policy analysis is adequate as a limitation/sensitivity table for a short paper. It spans `C_FP={1,2,5,10}`, fixes `C_FN=1`, and spans `C_REVIEW={0.02,0.1,0.5}`. It demonstrates that GB-18-GA is not universally preferred: it has lowest frozen-policy utility in 8/12 scenarios.

Limits:

- The GA was not retuned per scenario.
- The same sealed test outcomes were evaluated post hoc; the table must not be framed as selecting a new policy.
- A stronger follow-up would use a fresh audit set or repeated outer splits with pre-specified cost scenarios and separate validation-time policy selection.
