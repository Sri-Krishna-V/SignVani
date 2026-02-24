## Plan: Robustness Improvements for the ISL NLP Engine

Seven distinct problem areas were found. The plan is organized by effort-to-impact ratio — quick correctness fixes first, structural improvements second, and aspirational work last.

---

### Tier 1 — Quick Correctness Fixes (grammar_transformer.py)

**Step 1 — Add `had` to `PAST_AUXILIARIES`**
"He had eaten" currently leaks `HAVE` as a verb glyph. Add `'had'` → [grammar_transformer.py](nlp_backend/src/nlp/grammar_transformer.py#L30).

**Step 2 — Add a `MODAL_AUXILIARIES` set**
`could`, `would`, `should`, `might`, `may` are tagged `MD` (not `VB*`) so they fall into `subjects` as pre-verb nouns. Define `MODAL_AUXILIARIES = {'could', 'would', 'should', 'might', 'may'}` and suppress them in the token loop (similar to `PAST_AUXILIARIES`). Emit a `MAYBE` or `CONDITIONAL` tense marker if desired, or simply drop them for MVP.

**Step 3 — Fix `do`/`does` double-verb in statements**
`"I do not eat meat"` produces `I MEAT DO EAT NOT` because `do` is classified as a verb and shifts state. Extend the `QUESTION_AUXILIARIES` filter to also apply to sentences containing explicit `NEGATION_WORDS`, not just `ends_with_question` → [grammar_transformer.py](nlp_backend/src/nlp/grammar_transformer.py#L130).

**Step 4 — Remove the `adjectives = []` dead code**
This list is declared at [grammar_transformer.py line 106](nlp_backend/src/nlp/grammar_transformer.py#L106) but never populated or assembled. Either delete it or properly implement adjective collection and insert `adjectives` before the noun they modify in `isl_sequence`.

**Step 5 — Filter conjunctions (CC tag)**
`and`, `or`, `but` are not stopwords — they emit as nouns. Add a `CONJUNCTIONS = {'and', 'or', 'but', 'so', 'yet'}` set and `continue` past them in the token loop.

---

### Tier 2 — Contraction Coverage (text_processor.py)

**Step 6 — Expand the `CONTRACTIONS` map**
The current map at [text_processor.py lines 30–48](nlp_backend/src/nlp/text_processor.py#L30) covers only 14 negative contractions. Expand to cover:
- Subject + `be`: `I'm → I am`, `he's → he is`, `she's → she is`, `they're → they are`, `we're → we are`, `it's → it is`
- Subject + `have`: `I've → I have`, `we've → we have`, `they've → they have`
- Subject + `will`: `I'll → I will`, `he'll → he will`, `she'll → she will`, `they'll → they will`
- Misc: `let's → let us`, `that's → that is`, `there's → there is`
- Modal-have: `could've → could have`, `should've → should have`, `would've → would have`
- Missing negatives: `hadn't → had not`, `mightn't → might not`, `mustn't → must not`

This prevents corrupted tokens like `M`, `S`, `LL` from reaching the DB/avatar.

---

### Tier 3 — Contextual Relative Clause Detection (grammar_transformer.py)

**Step 7 — Don't treat relative `who/which` as question words**
`"The man who came is a doctor"` currently sets `question_type = 'WH'` and moves `who` to the end. A relative clause can be distinguished from a question by whether the sentence ends with `?`.

Apply a guard: if `ends_with_question` is False AND a question word occurs sentence-medially (not as first non-stopword), treat it as a relative pronoun and suppress it rather than routing into `question_markers`. This is the same `ends_with_question` flag that already exists on `ProcessedText`.

---

### Tier 4 — Time Expression Broadening (grammar_transformer.py)

**Step 8 — Expand `PAST_TIME_WORDS` and `FUTURE_TIME_WORDS`**
The tense-suppression logic at [grammar_transformer.py lines 195–200](nlp_backend/src/nlp/grammar_transformer.py#L195) currently only covers `yesterday` and `tomorrow`. Extend to obvious single-word past/future markers:
- Past: `yesterday`, `ago`, `previously`, `earlier`, `recently`, `formerly`
- Future: `tomorrow`, `soon`, `later`, `eventually`

Multi-word expressions (`last year`, `three days ago`) require a phrase-level pass before tokenizing — mark as a future enhancement.

---

### Tier 5 — Frontend Parity (islGlossConverter.js)

**Step 9 — Add tense detection to the frontend converter**
The offline converter at [islGlossConverter.js](client/src/Services/islGlossConverter.js) silently drops all tense. Add `PAST_AUXILIARIES`, `FUTURE_AUXILIARIES`, and VBD past-morphology detection (via `compromise`'s `.has('#PastTense')` check) matching the backend logic.

**Step 10 — Fix `will`/`shall` leaking as verb glosses**
These are `FUTURE_AUXILIARIES` in the backend but appear in no set in the frontend. They need to be consumed with a `FUTURE` marker, not emitted as verb glosses.

**Step 11 — Fix negation/question ordering divergence**
Backend places negation last: `[...verbs, ...question_markers, ...negations]`. Frontend reverses them. Align the frontend to match.

**Step 12 — Return metadata from frontend converter**
Add `tense`, `is_negated`, `question_type` to the object returned by `convertToISLGloss` so the UI gloss panel in `ConvertEnhanced` works correctly in offline mode too.

---

### Tier 6 — Number Handling

**Step 13 — Number-to-word conversion**
Add a utility `number_to_word()` function (using either the `num2words` library or a small hardcoded table for 0–100) that fires in `GlossMapper.process()` before the DB lookup. `"5"` → `"FIVE"` has a HamNoSys entry. Apply the same utility in the frontend converter.

---

### Tier 7 — Infrastructure & Memory

**Step 14 — Fix `GlossRetriever` LRU cache memory leak**
`@lru_cache` on an instance method at [retriever.py line 30](nlp_backend/src/database/retriever.py#L30) captures `self`, preventing GC. Move to a module-level `@lru_cache` keyed only on `(gloss: str)`, or use `functools.cached_property` properly.

**Step 15 — Add top-level error guard in `GlossMapper.process()`**
Wrap the body of `process()` in [gloss_mapper.py](nlp_backend/src/nlp/gloss_mapper.py) with a `try/except SignVaniError` that logs and returns a `GlossPhrase` with an empty glosses list and `error` field, instead of propagating exceptions to the API layer.

**Step 16 — Log (not silently swallow) FTS5 errors in `GlossRetriever`**
Bare `except: pass` at [retriever.py line 73](nlp_backend/src/database/retriever.py#L73) should at minimum call `logger.warning(...)` so DB degradation is observable in logs on RPi4.

---

### Tier 8 — Future / Aspirational

- **True fuzzy matching** using `spellfix1` extension or `rapidfuzz` for edit-distance gloss lookup
- **Passive voice detection** via `VBN + by-phrase` pattern for correct agent/patient reordering
- **VBN disambiguation** — distinguish `"was eaten"` (passive) from `"has eaten"` (perfect) using the preceding auxiliary
- **Multi-word time expression parsing** for "last year", "three days ago", "next week"
- **Vocabulary expansion** — `SWIM`, `DANCE`, `JUMP`, `RAIN`, `APPLE`, `MILK`, `HOSPITAL`, etc. are confirmed missing from `hamnosys_data.py`
- **Remove dead DB entry** — `DON'T` with apostrophe key in `hamnosys_data.py` is unreachable; remove or rename to `NOT`

---

### Verification

- Extend [tests/unit/test_text_input_rigorous.py](nlp_backend/tests/unit/test_text_input_rigorous.py) with cases for each tier (contractions, modals, relative clauses, compound conjunctions, numbers)
- Run `python -m tests.unit.test_nlp` and `python -m tests.unit.test_text_input_rigorous` for regression checks
- Manual spot-check on: `"She's going to school"`, `"I could have gone"`, `"The man who lives here is a doctor"`, `"I do not eat meat"`, `"Call 5 people"`

### Decisions

- Modal auxiliaries (`could`, `would`, `should`) — dropped silently for MVP rather than emitting a new grammatical marker (one less marker type for the UI and avatar to handle)
- Relative clause fix uses the existing `ends_with_question` flag — no new POS analysis needed, covers ~90% of cases at zero cost
- Number-to-word uses a hardcoded 0–100 table, not a new dependency, to stay within the RPi4 offline constraint
