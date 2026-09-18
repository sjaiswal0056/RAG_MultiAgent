# Project Learnings

## Retrieval needs complementary signals

Sparse retrieval was strongest for exact numeric clauses such as 25%, 40%, and waiting-period durations. Latent semantic retrieval helped with paraphrases such as home treatment versus domiciliary treatment. Reciprocal Rank Fusion kept either signal from dominating, while the separate pairwise reranker improved the final evidence ordering.

## Clause boundaries matter

Page-only or fixed-width chunks separated headings from rules and mixed unrelated clauses. Section-aware clause chunks produced stable, reviewable citations and made numeric validation possible.

## Agent boundaries improve auditability

Separating case planning, evidence retrieval, coverage analysis, decision synthesis, and validation made failures local. Each stage exchanges typed state, and the trace records actions and evidence identifiers without exposing private reasoning.

## Abstention is a product feature

Hospital eligibility, medical necessity, and short-duration domiciliary/day-care cases can be unsafe to decide from sparse facts. Explicit missing-evidence findings make NEEDS_REVIEW more useful than a low-confidence guess.

## Evaluation labels need context

The included expected outcomes are a candidate-authored scenario oracle based on the supplied case tasks and policy clauses, not insurer adjudications. Perfect agreement with this small set should not be treated as real-world accuracy.
