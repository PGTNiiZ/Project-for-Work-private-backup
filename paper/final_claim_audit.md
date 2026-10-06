# Final Claim-Evidence Audit

| Claim | Implementation evidence | Experimental evidence | Citation / basis | Status | Manuscript handling |
|---|---|---|---|---|---|
| Candidate generation reduces comparison space | Candidate workflow and frozen retrieval artifact | 449,149,239 to 2,086,245 pairs | [2], [7] for blocking context; artifact for values | Supported | Reported with counts |
| Blocking constrains downstream recall | Candidate workflow and evaluation harness | 25,931/29,243 positives covered; 3,312 misses | Artifact and [2], [7] | Supported | RQ3 limitation |
| GB-18-GA preserves the calibrated pair model | Policy consumes persisted GB-18 probabilities | GA code does not fit classifier/calibrator | Protocol/code audit | Supported | Explicit in Method |
| GB-18-GA improves F1 and recall vs GB-18 on LinkSocial outer splits | GA and repeated runner | F1 higher in 3/3 outer splits; mean F1 .8603 vs .8280 | Repeated artifacts | Supported within corpus | Qualified to LinkSocial/utility context |
| GB-18-GA reduces illustrative utility vs GB-18 | Utility implementation | Lower in 3/3 outer splits | Repeated artifacts | Supported for declared scenario | Not called business cost |
| GA increases FP and REVIEW vs GB-18 | Decision outputs | Higher in 3/3 outer splits | Repeated artifacts | Supported | Explicitly reported |
| MiniLM consistently improves linkage | GB-18 ablation exists | Mixed across outer splits | Repeated artifacts | Unsupported | Excluded; mixed result reported |
| GA/three-way ER is novel | Prior work exists | N/A | [3], [4] | Unsupported | Explicitly disclaimed |
| Results generalize beyond LinkSocial | One corpus only | No external corpus | N/A | Unsupported | Explicitly disclaimed |
| Utility represents measured CRM cost | No time study or elicitation | N/A | Internal audit | Unsupported | Called illustrative scenario |
| Human-review effectiveness or workload | Only offline REVIEW counts | No user study | N/A | Unsupported | Explicitly disclaimed |
| Dataset can be redistributed | No license found | N/A | Dataset provenance audit | Unsupported | Restricted-data statement |

Audit verdict: all quantitative and technical manuscript claims are traceable to the frozen research package. Unsupported claims are either removed or explicitly bounded.

## LaTeX packaging audit

The IEEE source preserves the same claim boundaries: it calls $U=2FP+FN+0.1REVIEW$ an illustrative operational scenario, explicitly reports the MiniLM mixed outer-split result, reports GA FP/REVIEW trade-offs, identifies blocking as a limitation, and restricts conclusions to LinkSocial. No new factual claim was introduced during conversion.
