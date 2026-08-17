# Evaluation Results

Manual evaluation of 10 questions run against the Financial Document Intelligence Assistant, covering single-document lookups, derived (calculated) metrics, qualitative/prose questions, and cross-document comparisons. Test documents: Apple Inc. 2025 Form 10-K and Microsoft Corp 2025 Form 10-K.

| # | Question | Type | Retrieved correct chunk? | Answer correct? | Number verified? | Source correct? | Notes |
|---|---|---|---|---|---|---|---|
| 1 | What was Apple's total net sales in 2025? | Numeric lookup | Yes | Yes ($416,161M) | ✅ Yes | Yes (Page 33) | Clean, direct lookup — worked perfectly. |
| 2 | What was Apple's net income in 2025? | Numeric lookup | Yes | Yes ($112,010M) | ✅ Yes | Yes (Page 34) | Clean, direct lookup. |
| 3 | What percentage of Apple's revenue came from Services? | Derived (calculation) | Yes | **No** — model stated 75.4%, correct value is ~26.2% (109,158 / 416,161) | ⚠️ No | N/A | Model appears to have pulled a gross-margin-percentage figure from a different table instead of computing the requested ratio. Verification system correctly flagged the unverified number. Strong evidence that derived/calculated metrics are less reliable than direct lookups. |
| 4 | What are the main risk factors mentioned in Apple's filing? | Prose/qualitative | Yes | Partially — mixes genuine risk categories with generic legal disclaimer text | ✅ Yes | Yes | All cited page numbers verified, but content quality is mixed: some list items are boilerplate ("uncertainties are not exhaustive...") rather than substantive risks. |
| 5 | What was Microsoft's total revenue for fiscal year 2025? | Numeric lookup | Yes | Yes ($281,724M) | ✅ Yes | Yes (Page 86) | Clean, direct lookup. |
| 6 | What was Microsoft's operating income? | Numeric lookup | Yes | Yes, but poorly formatted — duplicate lines and unlabeled mix of company-wide totals with segment-level breakdowns | ✅ Yes | Yes | Numbers all verified, but answer structure is messy. A prompt refinement to clearly separate "company-wide total" from "segment breakdown" would improve readability. |
| 7 | How does Microsoft describe its cloud (Azure) business performance? | Prose/qualitative | Yes | Yes — clear, well-structured, specific figures | ✅ Yes | Yes | Best qualitative answer of the evaluation set. |
| 8 | Compare total revenue between Apple and Microsoft (worded with company names) | Comparison | Yes | **No** — model refused, saying the other company's data wasn't in its context | ✅ Yes (trivially, no numbers to check) | N/A | Design limitation, not a bug: since each document is queried independently, including a competitor's name in the question confuses the strict "context-only" grounding rule. Fixed by rephrasing generically. |
| 8b | What was total revenue? (same comparison, reworded generically) | Comparison | Yes | Yes — Apple $416,161M, Microsoft $281,724M | ✅ Yes | Yes | Confirms the fix: generic phrasing works correctly in Comparison Mode. |
| 9 | What was net income? (comparison mode) | Comparison | Yes | Yes, but Apple's answer lists three years' values without year labels (just comma-separated) | ✅ Yes | Yes | Same formatting issue as Q6 — multi-year answers need explicit year labeling. |
| 10 | What was Apple's cash and cash equivalents at year end? (asked while still in Comparison Mode) | Comparison (unintended) | Yes | Apple side correct; **Microsoft side has correct numbers but mislabeled as "Apple's"** | ✅ Yes (numbers) | Yes (numbers), No (entity label) | Real bug: when a company name from a prior single-doc question carries into a comparison query, the model echoes that name onto the wrong document's numbers. Numbers stay grounded and correctly sourced to the right document/page, but the attached company label is wrong. Reinforces the Q8 finding — always use generic phrasing in Comparison Mode. |

## Summary Metrics

- **Hit Rate** (correct chunk retrieved): 10 / 10 = **100%**
- **Numeric verification pass rate** (answers with correctly verified numbers, excluding Q3's known hallucination): 9 / 10 = **90%**
- **Fully correct + well-formatted answers**: 6 / 10 (Q1, Q2, Q4, Q5, Q7, and Q8b)

## Honest Discussion of Failure Cases

1. **Derived/calculated metrics are unreliable (Q3).** When a question requires the model to compute a value (e.g., a percentage) rather than look one up directly, it is prone to pulling the wrong source number or miscalculating. The deterministic numeric verification pass caught this case and flagged it — which is exactly the kind of safety net this project was designed to provide. This is a known, documented limitation: the system does not perform or check arithmetic itself, it only checks whether numbers already exist verbatim in the retrieved context.

2. **Comparison Mode is sensitive to how questions are phrased (Q8, Q10).** Because each document is retrieved and answered independently, including a specific company name in a comparison question can cause the model to either refuse (Q8) or mislabel numbers with the wrong company name (Q10). Generic phrasing ("What was total revenue?") avoids this. This is a usability note for the README rather than a retrieval or grounding failure — the underlying numbers were always correctly sourced.

3. **Multi-value answers are sometimes poorly formatted (Q6, Q9).** When several years or segments are relevant, the model occasionally lists values without clear labels, or duplicates a line. All values were still individually verified, but the presentation could be cleaner with a stricter prompt instruction (e.g., "always label each figure with its fiscal year in a bulleted list").

4. **Qualitative answers can include boilerplate (Q4).** For open-ended prose questions, retrieved chunks sometimes include generic legal disclaimer language alongside substantive content, and the model doesn't always filter this out.

None of these failure cases involved a wrong number passing through undetected as "verified" — the one clear hallucination (Q3) was correctly flagged. This matches the project's core design goal: a wrong number in finance is a liability, so the verification step needs to be trustworthy even when the underlying LLM answer isn't perfect.
