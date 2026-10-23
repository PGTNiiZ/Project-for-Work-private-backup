# Baseline protocol (frozen before v2 execution)

Objective on POLICY_VALIDATION: `U = 2*FP + 1*FN + 0.1*REVIEW`. One objective evaluation scores one parameter vector over the complete policy-validation scored-pair array. Duplicate vectors count as evaluations.

| Baseline | Policy class | Validation tuned? | Optimizer | Free parameters | Evaluation budget |
|---|---|---|---|---|---|
| B0 | Fixed simple thresholds | No | None | 0; `(t_match,t_review)=(0.98,0.95)` | 0 |
| B1 | Simple two-threshold policy | Yes, policy-validation only | Deterministic Sobol | `t_match,t_review` | same declared Sobol budget, measured and recorded |
| B2 | Expanded four-parameter policy | Yes, policy-validation only | Deterministic Sobol | `t_match,t_review,c_promote,c_demote` | exactly B3 realized count |
| B3 | Expanded four-parameter policy | Yes, policy-validation only | Existing seeded GA | `t_match,t_review,c_promote,c_demote` | instrumented realized count |

B2 and B3 use identical decision semantics, bounds, objective, data, and policy-validation role. The v1 nominal GA budget is population 60 × generations 40 = 12,000, but v2 records the actual count including initialization and generation behavior; B2 receives that exact count. Seeds 101, 202, and 303 are fixed before execution. No stopping criterion may depend on SEALED_TEST results.

Tie-breaking is deterministic and predeclared: candidate policies are retained in generation order when objective values tie (strict improvement only); for independent GA trial selection, the smallest GA seed wins an equal validation-cost tie. No test value participates in a tie.

Policy bounds: `t_match ∈ [0.90,0.999]`, `t_review ∈ [0.50,t_match]`, `c_promote ∈ [0.50,1.0]`, `c_demote ∈ [0,c_promote]`.
