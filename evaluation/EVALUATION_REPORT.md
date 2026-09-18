# Evaluation Report

## Method

`python scripts/run_evaluation.py` rebuilds the policy index, loads 12 supplied public cases and 5 candidate-created cases, runs the same workflow for every case, and writes JSON results. Expected decisions and evidence concepts are defined in `expected_outcomes.json`. They were established by manual reading of the supplied policy and each synthetic scenario; they are a candidate-authored scenario oracle, not insurer adjudications.

Evidence recall@k is a case-level hit: every expected concept group must have at least one matching term in a returned citation. Citation coverage is cited material findings divided by material findings. Citation support combines metadata validation, lexical overlap, and numeric presence. This is controlled verification, not a general natural-language-inference benchmark.

## Latest results

| Metric | Public | Candidate | Combined |
|---|---:|---:|---:|
| Cases | 12 | 5 | 17 |
| Decision agreement | 1.0000 | 1.0000 | 1.0000 |
| Evidence recall@k | 1.0000 | 1.0000 | 1.0000 |
| Citation coverage | 1.0000 | 1.0000 | 1.0000 |
| Citation support | 1.0000 | 1.0000 | 1.0000 |
| Correct abstentions | 3/3 | 2/2 | 5/5 |
| Unsafe answers when abstention expected | 0 | 0 | 0 |
| Unnecessary abstentions | 0 | 0 | 0 |

The combined run produced 113 material findings, all linked to citations, with 119 valid citations and no invalid citation metadata. Perfect agreement is expected for this deliberately small development suite and should not be extrapolated.

## Observed failures and improvements

### Direct script could not import the application

- Observed behavior: `python scripts/build_index.py` raised `ModuleNotFoundError: app`.
- Root cause: running a file directly put `scripts/`, not the repository root, first on the import path.
- Impact: documented build and evaluation commands were not reproducible.
- Change made: each direct entry point inserts the resolved repository root before application imports.
- Before: the index command failed immediately.
- After: it builds 179 chunks across all 17 pages.
- Remaining limitation: module execution is cleaner in packaged installations, but the assignment requires direct script commands.

### Ordinary claims abstained for missing medical necessity

- Observed behavior: PUB-001 returned `NEEDS_REVIEW` even though the case did not explicitly mark medical necessity unknown.
- Root cause: the agent treated an absent `medical_necessity_confirmed` key as an explicit null value.
- Impact: false abstention on otherwise supported claims.
- Change made: missing-evidence logic now triggers only when the case explicitly includes that key with a null value.
- Before: PUB-001 abstained.
- After: PUB-001 returns `ADMISSIBLE_WITH_LIMITS`; PUB-006 still abstains as intended.
- Remaining limitation: document names are not equivalent to document-content verification.

### Broad limit query missed exact numeric clauses

- Observed behavior: the first evaluation reached 0.8235 evidence recall because the 25%/40% clauses were sometimes below the rerank cutoff.
- Root cause: one broad expense query mixed room, practitioner, medicines, diagnostics, and ambulance concepts; similarly scored chunks displaced exact clauses.
- Impact: decisions could cite an incomplete set of category limits.
- Change made: the planner now issues four focused limit queries, tokenization normalizes simple plurals, and the rerank window is ten.
- Before: combined evidence recall@k was 0.8235.
- After: it is 1.0000 on the 17-case suite.
- Remaining limitation: rare paraphrases may still require a learned cross-encoder or curated query expansion.

### Per-citation lexical validation caused false failures

- Observed behavior: adding strict lexical support checking caused supported cases to fall to `NEEDS_REVIEW`.
- Root cause: multiple citations were attached to one claim even when only one carried the exact numeric clause; the validator correctly flagged the weaker citation.
- Impact: 12 unnecessary abstentions in an intermediate run.
- Change made: each material finding now cites its highest-ranked supporting chunk, and focused retrieval ensures that chunk contains the numeric rule.
- Before: combined decision agreement was 0.2941 in the intermediate run.
- After: combined agreement is 1.0000 with zero unnecessary abstentions.
- Remaining limitation: lexical overlap is not a full contradiction/entailment model.

## Limitations

The expected outcomes are not independent labels. LSA is corpus-local and the deterministic cross-feature reranker is less capable than a fine-tuned neural cross-encoder. Citation semantic support uses controlled lexical/numeric verification. The prototype does not inspect the contents of uploaded medical documents, policy schedules, endorsements, remaining sum-insured history, or insurer systems. Such gaps must remain human-review conditions in production.
