# ID Changelog — v1 → v2

หลักการ: คง ID ของ v1 ไว้เสมอที่เป็นไปได้; ไม่มีการ renumber · แหล่งความจริง: `design/HYPOTHESIS_EXPERIMENT_MATRIX.csv` (คอลัมน์ `v2_id_status`)

| ID | v1 | v2 | ประเภทการเปลี่ยน | เหตุผล / หลักฐาน |
|---|---|---|---|---|
| E2-2 | Historical rule replica (R0 formula) | **RETIRED → E6-1** | ยุบ | R0 = threshold 0.98/0.95 บน score ของโมเดล ไม่ใช่สูตร lexical [MAIN@1e0a2db:train_data/stage15_crm_entity_pipeline/run_crm_entity_pipeline.py#L117-L127]; rule มือ stage18 = policy 4 ยีน [MAIN@1e0a2db:exp_r1_ga_redecision.py#L18] |
| E5-2 | Semantic-only fusion (= E4-2) | **ALIAS → E4-2** | แก้ duplicate | v1 ระบุว่าเป็น run เดียวกัน |
| E5-1 | Lexical-only fusion | **ALIAS → E3-2 (GBDT) / E3-1 (LR)** | แก้ duplicate (ใหม่) | config เหมือนกันทุกประการ |
| E4-2 | Semantic-only classifier | KEPT (absorbs E5-2); core → SUPPORTING | priority | ไม่ใช่ primary contrast |
| E1-1 | Standard/exact key blocking | KEPT; ระบุ spec ครบจาก repo | spec | [MAIN@1e0a2db:train_data/stage7_14_full_candidate_pipeline/run_full_candidate_pipeline.py#L35, #L118-L179] |
| E1-2 | core (Optional-in-MVP) | KEPT → CONDITIONAL | priority | อาจซ้ำ E1-3 |
| E1-6 | optional | KEPT → CONDITIONAL | priority | trigger เมื่อ best PC < 0.90 |
| E3-1 | core | KEPT → SUPPORTING | priority | H2 primary = GBDT |
| E5-4 | core | KEPT → SUPPORTING | priority | explanatory |
| E6-1 | Fixed threshold | KEPT; absorbs E2-2 (R0 + stage18 rules) → SUPPORTING | scope | — |
| E6-3 | Closed-form cost threshold | KEPT; + Chow three-way rule | scope | [BACKUP@903246c:experiments/code/reviewer_revision.py] |
| E6-4 | Random + TPE (2,000) | KEPT; + scrambled Sobol; budget 2,048 | scope | ICSEC v2 baseline; Sobol 2^m |
| E6-5 | GA (2,000) | KEPT; genome 4 ยีนเดิม; budget 2,048 | scope | [MAIN@1e0a2db:exp_r1_ga_redecision.py#L75-L113] |
| E6-6 | core | KEPT → SUPPORTING | priority | H4c secondary |
| E6-8, E4-3, E4-4 | optional (conditional) | KEPT → CONDITIONAL | label | — |
| E7-3…E7-7 | core | KEPT → SUPPORTING | priority | ไม่ใช่ primary contrast |
| E9-1, E10-1 | optional | KEPT → CONDITIONAL | label | มีเงื่อนไขชัด (coverage / 1:n) |
| E2-4, E3-3, E4-5, E5-6, E8-1…E8-3 | optional | KEPT → OPTIONAL | label | — |
| D0-1 | Label provenance audit | KEPT; ขยายครอบคลุม LinkSocial provenance + label-proxy | scope | [P38] |
| D0-4 | Leakage audit | KEPT; + historical test exposure | scope | R-15 |
| **D0-5** | — | **NEW (OPTIONAL)** historical artifact re-analysis | เพิ่ม | DQ7 |

ไม่มี ID ที่ถูกเปลี่ยนหมายเลข · ไม่มี hypothesis ID ใหม่ (H1–H5 คงเดิม; DQ7 ใหม่)
