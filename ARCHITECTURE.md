# Architecture

## Boundaries and state flow

The application uses a custom, typed state machine. `ClaimWorkflowState` carries the validated case, investigation plan, ranked evidence, specialist findings, decision draft, validation result, trace, errors, and retry count. Five specialized agents operate in sequence:

1. Case Analysis normalizes facts, detects relevant dimensions and missing evidence, and creates several focused queries.
2. Policy Evidence executes dense LSA and BM25 retrieval, fuses rankings with Reciprocal Rank Fusion, and reranks query-document pairs.
3. Coverage and Exclusion converts evidence into typed findings for definitions, cover, waiting periods, portability, exclusions, limits, windows, and evidence requirements.
4. Decision combines findings and deterministic arithmetic into one allowed status.
5. Validation checks citation identity and metadata, material-claim coverage, lexical support, numeric consistency, and decision safety.

Validation can return a draft for one controlled retry. A remaining failure becomes `NEEDS_REVIEW` rather than an unsupported answer.

## Ingestion and retrieval

The PDF loader preserves page numbers. Cleaning removes repeated headers while retaining clause text. The chunker tracks major headings and starts new chunks at numbered clauses, definitions, notes, and bullets. Stable identifiers combine page, heading slug, ordinal, and a text digest.

Dense retrieval uses local Latent Semantic Analysis: TF-IDF document-term values are projected with truncated singular-value decomposition into normalized dense vectors. It requires no network or model download. An optional cached SentenceTransformer backend can be selected with `EMBEDDING_BACKEND=sentence_transformers`. Sparse retrieval uses an in-repository BM25 implementation with consistent tokenization and light plural normalization.

RRF computes the sum of `1 / (k + rank)` across dense and sparse rankings and deduplicates by chunk ID. The cross-feature reranker is a real second stage, jointly scoring each query-document pair using query coverage, heading overlap, phrase matches, and numeric matches. It records pre-rerank position, score, and final rank.

## Evidence contract and arithmetic

Every non-uncertain finding must cite an indexed chunk. Citations contain source, PDF page, section, chunk ID, and excerpt. The validator rejects unknown IDs, mismatched metadata, claims with no citation, weak lexical support, and numeric statements absent from cited text.

Payable estimates are deterministic. Room, practitioner, medicines/diagnostics, ambulance, pre/post windows, domiciliary caps, and overall Sum Insured are computed in Python. No LLM performs arithmetic. The estimate is omitted when evidence is insufficient or validation fails.

## Confidence and abstention

Confidence is a bounded heuristic based on evidence count, uncertainty, and validation status. It is not a calibrated probability. Missing hospital-definition proof, missing medical necessity, unresolved domiciliary duration, or unverified sub-24-hour eligibility creates an uncertain finding and forces `NEEDS_REVIEW / INSUFFICIENT_EVIDENCE`.

## Trade-offs

Local LSA and cross-feature reranking are small, deterministic, and deployment-friendly, but weaker than a fine-tuned embedding and cross-encoder stack on broad paraphrases. The policy logic is intentionally narrow and policy-specific; it does not use medical knowledge. The candidate-authored evaluation oracle tests expected scenarios but is not an independent insurer-labeled benchmark.
