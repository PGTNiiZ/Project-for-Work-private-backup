# Literature Search Log

Search date: 2026-09-02. Scope: the frozen question of calibrated profile-pair scores followed by a GA-selected MATCH/REVIEW/NO_MATCH policy, plus entity-disjoint evaluation and blocking error decomposition.

## Search record

| Query | Database / access route | Inclusion reason | Exclusion reason / outcome |
|---|---|---|---|
| `"entity resolution" AND (blocking OR filtering)` | ACM Digital Library | Found the survey that establishes candidate reduction as a separate ER stage | Included: Papadakis et al., DOI 10.1145/3377455 |
| `"record linkage" AND "three-way decision"` | ScienceDirect / Crossref | Exact three-way-record-linkage terminology | Included: Ouyang et al., DOI 10.1016/j.eswa.2018.12.038 |
| `"genetic algorithm" AND "entity resolution"` | SpringerLink / Crossref | Exact evolutionary-ER terminology | Included: Sun et al., DOI 10.1007/s11704-015-5276-6 |
| `"user identity linkage" "profile features"` | ACM Digital Library | Direct social-profile linkage comparator | Included: Yao, DOI 10.1145/3650400.3650622 |
| `"record linkage" AND evaluation AND threshold` | ACM Digital Library | Application-dependent error trade-offs / evaluation | Included: Christen et al., DOI 10.1145/3786768 |
| `"entity resolution" AND (genetic OR evolutionary) AND (three-way OR reject OR review) AND (cost OR utility OR threshold)` | Google Scholar-style web index and general web search | Exact proposed-method intersection | No verified exact prior combination found; this is not proof of absence |
| `"calibrated probability" "entity matching"` | Google Scholar-style web index and general web search | Checks whether calibrated scores are optimized by GA review policies | No directly comparable verified paper found |
| `"sentence embeddings" AND (entity matching OR record linkage OR profile matching)` | Google Scholar-style web index and arXiv | Identified transformer record-linkage tooling/relevant representation literature | LinkTransformer preprint found; not included as a primary comparator because no verified equivalent policy evaluation was obtained |
| `"entity-disjoint" "record linkage" evaluation` | Google Scholar-style web index | Searches for strict split methodology | No directly comparable peer-reviewed study verified from accessible results; do not claim the first such split |
| `"blocking miss" entity resolution scoring error` | ACM / Springer / general web | Searches for explicit retrieval-to-decision decomposition | Blocking surveys support candidate recall concerns; no exact comparable decomposition verified |
| `"LinkSocial" dataset license` | GitHub, IEEE Xplore, web index | Dataset provenance and reuse conditions | Included authoritative GitHub dataset repository; no license found |
| `"LinkSocial: Linking User Profiles Across Multiple Social Media Platforms"` | IEEE Xplore, GitHub, Crossref/web index | Dataset/publication identity | Included IEEE record 8588801 and official public repository |

## Database coverage limitations

- IEEE Xplore was searched through its public record/PDF index for LinkSocial and broad query results. Full-text/query export access was not available.
- ACM DL, SpringerLink, Elsevier/ScienceDirect landing pages, Crossref metadata, public GitHub, arXiv, and web-indexed Google Scholar-style results were directly inspected.
- Scopus and Web of Science were not accessible from this environment. No claim of exhaustive proprietary-index coverage is made.

## Inclusion rules

A work was included in `related_work_verified_v2.md` only when title, authors, year, venue, and DOI/stable identifier were verified through publisher or Crossref metadata, and it materially addressed at least one of: ER blocking, social-profile linkage, three-way linkage, evolutionary ER, or ER evaluation under operational error trade-offs.

## Exclusion rules

Excluded from the core comparison were vendor pages, patents, generic reject-option studies outside linkage, unverified ResearchGate-only records, and papers whose metadata/method could not be independently confirmed. They may be used only as discovery leads, not citations.
