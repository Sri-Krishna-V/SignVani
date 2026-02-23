# ISL Grammar Enhancement — Tense, Negation, Questions

Three incremental phases add ISL-specific grammar intelligence to the NLP backend pipeline. Phase 1 detects tense from auxiliaries/morphology and inserts `PAST`/`FUTURE` markers at the start of the gloss sequence. Phase 2 expands contractions, repositions negation to the sentence end (ISL convention), and annotates negation in the API response. Phase 3 classifies sentences as WH-question, yes/no-question, or statement, moves WH-words to the end, and annotates question type. All changes stay in the NLP backend (`nlp_backend/`); no avatar/frontend changes. Each phase ships independently with its own tests.

---

## Shared Refactor: `transform()` Return Type

Done in Phase 1 to avoid API churn across phases.

- Change `GrammarTransformer.transform()` to return `(List[str], GrammarMetadata)` instead of `List[str]`
- Add `GrammarMetadata` as a new `__slots__` dataclass in `nlp_backend/src/nlp/dataclasses.py`:
  - `tense: Optional[str]` — values: `None`, `"PAST"`, `"FUTURE"`
  - `is_negated: bool`
  - `question_type: Optional[str]` — values: `None`, `"WH"`, `"YES_NO"`
- `GlossMapper.process()` unpacks the tuple, passes metadata to `GlossPhrase`
- Phases 2 and 3 incrementally populate more fields of `GrammarMetadata`
- Export `GrammarMetadata` from `nlp_backend/src/nlp/__init__.py`

---

## Phase 1 — Tense Markers

### Problem
`GrammarTransformer.STOPWORDS` includes `was`, `were`, `been`, `being` — these carry tense information that is silently discarded. `will`/`shall` get mis-classified as main verbs. ISL requires an explicit time reference at the sentence start.

### Changes

**`nlp_backend/src/nlp/grammar_transformer.py`**

1. Remove `was`, `were`, `been` from `STOPWORDS`
2. Add class constants:
   ```python
   PAST_AUXILIARIES = {'was', 'were', 'been', 'did'}
   FUTURE_AUXILIARIES = {'will', 'shall'}
   PRESENT_AUXILIARIES = {'is', 'am', 'are', 'be', 'being'}  # already in STOPWORDS, no marker
   ```
3. During the token loop:
   - When token matches `PAST_AUXILIARIES` → set `detected_tense = 'PAST'`, skip token (suppress from output)
   - When token matches `FUTURE_AUXILIARIES` → set `detected_tense = 'FUTURE'`, skip token
4. Also detect past tense from verb POS morphology — if no auxiliary was found but a verb is tagged `VBD` or `VBN`, set `detected_tense = 'PAST'` (covers "I went to school")
5. Output order: `[PAST|FUTURE] + Time + Subject + Object + Verb + Negation + Question`
6. Return `(isl_sequence, GrammarMetadata(tense=detected_tense, ...))`

**`nlp_backend/src/nlp/dataclasses.py`**

- Add `GrammarMetadata` class with `__slots__ = ('tense', 'is_negated', 'question_type')`
- Extend `GlossPhrase.__slots__` with `tense`, `is_negated`, `question_type`
- Update `GlossPhrase.__init__` and `__repr__`

**`nlp_backend/src/nlp/gloss_mapper.py`**

- Unpack `(raw_glosses, metadata)` from `grammar_transformer.transform()`
- Pass `tense=metadata.tense`, `is_negated=metadata.is_negated`, `question_type=metadata.question_type` into `GlossPhrase(...)`

**`nlp_backend/src/database/hamnosys_data.py`**

- Add a `TIME_MARKERS` category with placeholder HamNoSys strings:
  ```python
  'PAST':   'hamflathand,hampalmd,...',
  'FUTURE': 'hamflathand,hampalmu,...',
  ```

**`nlp_backend/api_server.py`**

- Add `"tense": gloss_phrase.tense` to JSON responses of `/api/text-to-sign` and `/api/text-to-handsign`

### Tests (add to `nlp_backend/tests/unit/test_nlp.py`)

- `test_past_tense_auxiliary` — "I was eating" → glosses contain `PAST`, SOV order preserved
- `test_past_tense_verb_morphology` — "I went to school" → `["PAST", "I", "SCHOOL", "GO"]`
- `test_future_tense` — "I will go to market" → `["FUTURE", "I", "MARKET", "GO"]`
- `test_present_tense_no_marker` — "I eat rice" → `["I", "RICE", "EAT"]`, no tense marker
- `test_tense_with_time_word` — "Yesterday I was playing" → `["PAST", "YESTERDAY", "I", "PLAY"]`

---

## Phase 2 — Negation

### Problem
- Contractions like `don't` are not split before processing; `n't` is in `NEGATION_WORDS` but NLTK tokenises `don't` → `do` + `n't` (with apostrophe), so it may never match
- Current output order places negation after verbs, but ISL negation goes at the **end** of the clause
- `is_negated` is not surfaced in the API response

### Changes

**`nlp_backend/src/nlp/text_processor.py`**

Add a `CONTRACTIONS` dict and a pre-tokenisation expansion pass (before lowercasing):
```python
CONTRACTIONS = {
    "don't": "do not",  "doesn't": "does not", "didn't": "did not",
    "can't": "can not", "won't":   "will not",  "isn't":  "is not",
    "aren't": "are not", "wasn't": "was not",   "weren't": "were not",
    "haven't": "have not", "hasn't": "has not", "couldn't": "could not",
    "shouldn't": "should not", "wouldn't": "would not",
}
```
Apply with `re.sub` in `process()` before the tokenise step.

**`nlp_backend/src/nlp/grammar_transformer.py`**

1. Change output order to: `[Tense] + Time + Subject + Object + Verb + Question + Negation`
   (Negation is now the final modifier — ISL convention)
2. If `negations` list has > 1 item, collapse to a single `NOT` (avoid double negation)
3. Set `GrammarMetadata.is_negated = bool(negations)` before discarding duplicates
4. `did` (already in `PAST_AUXILIARIES`) is stripped after triggering tense detection, so "I didn't eat" → `["PAST", "I", "EAT", "NOT"]`

**`nlp_backend/api_server.py`**

- Add `"is_negated": gloss_phrase.is_negated` to JSON responses

### Tests

- `test_contraction_expansion` — "I don't like cats" → tokens contain `not`, `like`, `cat`
- `test_negation_at_end` — "I don't eat meat" → `["PAST", "I", "MEAT", "EAT", "NOT"]`
- `test_never` — "I never go there" → `["I", "GO", "NEVER"]`
- `test_negative_question` — "Don't you like it?" — verify ISL-correct order of question and negation

---

## Phase 3 — Question Types

### Problem
- WH-words are moved to the end correctly, but there is no distinction between WH-questions and yes/no questions
- ISL uses different non-manual markers: furrowed brow for WH-questions, eyebrow raise for yes/no questions
- Y/N questions are not detected at all; the NLP produces plain SOV output with no annotation

### Changes

**`nlp_backend/src/nlp/text_processor.py`**

- Before replacing `?`, check `original_text.strip().endswith('?')` and store as `ends_with_question: bool`
- Add `ends_with_question` to `ProcessedText.__slots__` and pass it through

**`nlp_backend/src/nlp/grammar_transformer.py`**

Question type detection logic in `transform()`:

```python
YES_NO_AUX = {'do', 'does', 'did', 'is', 'are', 'am', 'was', 'were',
              'can', 'could', 'will', 'would', 'shall', 'should', 'have', 'has', 'had'}

if question_markers:
    detected_question_type = "WH"
elif processed_text.ends_with_question:
    # Check if first content token is a yes/no auxiliary
    first_token = processed_text.tokens[0].lower() if processed_text.tokens else ''
    if first_token in YES_NO_AUX:
        detected_question_type = "YES_NO"
    else:
        detected_question_type = "YES_NO"   # question mark alone is sufficient signal
else:
    detected_question_type = None
```

Set `GrammarMetadata.question_type = detected_question_type`.

**`nlp_backend/src/nlp/dataclasses.py`**

- Add `ends_with_question: bool` to `ProcessedText.__slots__` and `__init__`
- `GlossPhrase.question_type` already added in Phase 1 shared refactor

**`nlp_backend/api_server.py`**

- Add `"question_type": gloss_phrase.question_type` to JSON responses

### Tests

- `test_wh_question` — "What is your name?" → `question_type == "WH"`, `WHAT` at end of glosses
- `test_yn_question` — "Do you like coffee?" → `question_type == "YES_NO"`, SOV output `YOU COFFEE LIKE`
- `test_statement_no_question` — "I like coffee" → `question_type is None`
- `test_yn_question_with_future` — "Will you come tomorrow?" → `question_type == "YES_NO"`, `tense == "FUTURE"`

---

## Files Changed Summary

| File | Phase 1 | Phase 2 | Phase 3 |
|------|---------|---------|---------|
| `nlp_backend/src/nlp/dataclasses.py` | Add `GrammarMetadata`; extend `GlossPhrase` slots | `is_negated` field | `ends_with_question` on `ProcessedText` |
| `nlp_backend/src/nlp/grammar_transformer.py` | Split auxiliaries, detect tense, new return type | Reorder negation to end, dedup, `is_negated` | Detect WH vs Y/N, `question_type` |
| `nlp_backend/src/nlp/text_processor.py` | — | Contraction expansion dict + `re.sub` pass | `ends_with_question` flag |
| `nlp_backend/src/nlp/gloss_mapper.py` | Unpack metadata tuple, pass to `GlossPhrase` | Pass `is_negated` | Pass `question_type` |
| `nlp_backend/src/nlp/__init__.py` | Export `GrammarMetadata` | — | — |
| `nlp_backend/src/database/hamnosys_data.py` | Add `PAST`/`FUTURE` glosses under `TIME_MARKERS` | — | — |
| `nlp_backend/api_server.py` | Add `tense` to responses | Add `is_negated` | Add `question_type` |
| `nlp_backend/tests/unit/test_nlp.py` | 5 new test cases | 4 new test cases | 4 new test cases |

---

## Verification

After each phase:

```bash
cd nlp_backend
python -m tests.unit.test_nlp
python -m tests.integration.test_pipeline_phase1_2
```

Manual API spot-checks:

```bash
# Phase 1
curl -X POST http://localhost:8000/api/text-to-sign \
  -H "Content-Type: application/json" \
  -d '{"text": "I was going to the market"}'
# expect: tense: "PAST", glosses start with PAST

# Phase 2
curl -X POST http://localhost:8000/api/text-to-sign \
  -H "Content-Type: application/json" \
  -d '{"text": "I don'\''t eat meat"}'
# expect: is_negated: true, NOT at end of glosses

# Phase 3
curl -X POST http://localhost:8000/api/text-to-sign \
  -H "Content-Type: application/json" \
  -d '{"text": "Do you like coffee?"}'
# expect: question_type: "YES_NO"
```

---

## Decisions Log

- **Tense approach**: Time-word (PAST/FUTURE marker at sentence start, ISL convention)
- **Classifiers**: Deferred to a later iteration
- **Non-manual markers**: NLP annotations only (`question_type`, `is_negated` in API response); avatar facial/head animation deferred
- **Contraction expansion**: Done in `TextProcessor` (pre-tokenisation) — NLTK's POS tagger handles full forms better than `n't` fragments
- **Double negation**: Collapsed to single `NOT` in output
