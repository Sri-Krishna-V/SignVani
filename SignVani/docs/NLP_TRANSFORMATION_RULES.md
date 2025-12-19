# NLP Transformation Rules: English to ISL

This document outlines the linguistic rules used by SignVani to convert Standard English into Indian Sign Language (ISL) Gloss.

## 1. Sentence Structure (Syntax)

ISL primarily follows the **Subject-Object-Verb (SOV)** word order, unlike English which follows Subject-Verb-Object (SVO).

### Rule: SVO -> SOV

**English**: Subject + Verb + Object
**ISL**: Subject + Object + Verb

**Examples**:
- English: *I am going to the market.*
  - Subject: I
  - Verb: am going (go)
  - Object: market
  - **ISL Gloss**: I MARKET GO

- English: *He plays cricket.*
  - Subject: He
  - Verb: plays (play)
  - Object: cricket
  - **ISL Gloss**: HE CRICKET PLAY

## 2. Time Markers

In ISL, time markers (yesterday, tomorrow, now, 5pm) usually come at the **beginning** of the sentence to set the context.

**Rule**: [Time] + [Subject] + [Object] + [Verb]

**Examples**:
- English: *I will go to school tomorrow.*
  - **ISL Gloss**: TOMORROW I SCHOOL GO

## 3. Question Words (Wh-words)

Question words (What, Where, Who, When, Why, How) typically come at the **end** of the sentence.

**Rule**: [Subject] + [Object] + [Verb] + [Question Word]?

**Examples**:
- English: *What is your name?*
  - **ISL Gloss**: YOUR NAME WHAT?

- English: *Where are you going?*
  - **ISL Gloss**: YOU GO WHERE?

## 4. Negation

Negation words (not, no, never) usually follow the verb or come at the end.

**Rule**: [Subject] + [Object] + [Verb] + [Negation]

**Examples**:
- English: *I do not like apples.*
  - **ISL Gloss**: I APPLE LIKE NOT

## 5. Stop-Word Removal

ISL is a concise language and omits many auxiliary words used in English grammar.

**Removed Words**:
- **Articles**: a, an, the
- **Auxiliary Verbs**: is, am, are, was, were, be, been (unless used as main verb "exist")
- **Prepositions**: to, of, for, with, by (often incorporated into the sign directionality)

**Examples**:
- English: *The cat is sleeping on the mat.*
  - **ISL Gloss**: CAT MAT SLEEP

## 6. Lemmatization (Root Forms)

Verbs are usually signed in their root (infinitive) form. Tense is indicated by time markers or context, not by modifying the verb sign itself.

**Rule**: Convert inflected verbs to root form.

**Examples**:
- *Going* -> GO
- *Played* -> PLAY
- *Sleeping* -> SLEEP
- *Better* -> GOOD (plus facial expression)

## 7. Pluralization

Plurals are often indicated by:
1. **Repetition**: Signing the word twice (e.g., TREE TREE for "forest" or "trees").
2. **Quantifiers**: Adding numbers or words like MANY.
3. **Sweep**: Moving the hand in a sweep (e.g., for "audience").

*Note: Current SignVani implementation primarily uses the singular root form unless a specific plural sign exists.*

## Implementation in SignVani

The `NLPPipeline` class implements these rules using:
1. **spaCy**: For Part-of-Speech (POS) tagging and Dependency Parsing to identify Subject, Object, and Verb.
2. **NLTK**: For stop-word removal and lemmatization.
3. **Custom Logic**: For reordering tokens into SOV format.
