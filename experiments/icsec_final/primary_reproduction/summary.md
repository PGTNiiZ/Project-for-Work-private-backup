# GB-17 / GB-18 / GB-18-GA Experiment

Nested entity-aware split seed 42; outer test remained sealed until final evaluation.
GB configuration: GradientBoostingClassifier(n_estimators=300, learning_rate=0.05, max_depth=6, random_state=42).

## Test comparison

| Experiment | TP | FP | FN | REVIEW | Precision | Recall | F1 | Weighted cost |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| R0 | 5864 | 88 | 1689 | 8783 | 0.9852 | 0.6683 | 0.7964 | 2304.6600 |
| R3 | 6689.6000 | 66.0000 | 1565.0000 | 1119.4000 | 0.9902 | 0.7624 | 0.8615 | 1917.3880 |
| GB-17 | 3736 | 19 | 1976 | 3192 | 0.9949 | 0.4258 | 0.5963 | 2333.2000 |
| GB-18 | 6391 | 75 | 1831 | 623 | 0.9884 | 0.7283 | 0.8387 | 2043.3000 |
| GB-18-GA | 6730 | 107 | 1565 | 847 | 0.9843 | 0.7670 | 0.8622 | 1863.7000 |

Winner by weighted cost: **GB-18-GA**.

## Isolated effects (right minus left; cost reduction is positive when cost falls)

### GB-17_to_GB-18_MiniLM_effect

TP=2655.0000, FP=56.0000, FN=-145.0000, REVIEW=-2569.0000, precision=-0.0065, recall=0.3025, F1=0.2424, cost=-289.9000, cost_reduction=289.9000

### GB-18_to_GB-18-GA_decision_layer_effect

TP=339.0000, FP=32.0000, FN=-266.0000, REVIEW=224.0000, precision=-0.0041, recall=0.0387, F1=0.0235, cost=-179.6000, cost_reduction=179.6000

### R3_to_GB-18-GA_model_family_effect

TP=40.4000, FP=41.0000, FN=0.0000, REVIEW=-272.4000, precision=-0.0059, recall=0.0046, F1=0.0007, cost=-53.6880, cost_reduction=53.6880

## GA validation seeds

Test metrics were not calculated per GA seed. The selected seed/genome was chosen from ga_validation weighted cost only, then evaluated on test once.

| Seed | Validation cost | t_m | t_r | c_promote | c_demote |
|---:|---:|---:|---:|---:|---:|
| 7 | 590.00 | 0.980817 | 0.608610 | 0.956252 | 0.258878 |
| 42 | 590.00 | 0.973932 | 0.594044 | 0.956599 | 0.137870 |
| 123 | 590.00 | 0.972677 | 0.602718 | 0.956269 | 0.153879 |
| 999 | 589.80 | 0.979888 | 0.603575 | 0.956125 | 0.656159 |
| 2025 | 590.00 | 0.980051 | 0.592344 | 0.956127 | 0.244231 |

Selected seed: 999; selected validation cost: 589.80.
Selected genome: `{"c_demote": 0.6561585668398386, "c_promote": 0.9561245224549983, "t_m": 0.9798877883476613, "t_r": 0.6035751931953067}`.

## Verification

- GB-17 and GB-18 share the same sampled training pair hash, labels, model seed, and hyperparameters.
- GB-18 manual and GB-18-GA use the same `gb18_probabilities.parquet` artifact.
- Test labels were not accessed before final selection; drop pairs were excluded.
- See `artifact_hashes.json` for SHA-256 hashes.
