/**
 * ISL Gloss Converter
 *
 * Client-side port of the SignVani NLP pipeline:
 *   TextProcessor → GrammarTransformer → GlossMapper
 *
 * Converts English text (SVO order) to Indian Sign Language gloss sequence (SOV order).
 * Uses the 'compromise' library for tokenisation, POS tagging, and lemmatisation.
 *
 * Pipeline:
 *   text → processText() → transformToSOV() → UPPERCASE glosses[]
 *
 * Ported from:
 *   nlp_backend/src/nlp/grammar_transformer.py
 *   nlp_backend/src/nlp/text_processor.py
 *   nlp_backend/src/nlp/gloss_mapper.py
 */
import nlp from 'compromise';

// ── Word sets ────────────────────────────────────────────────────────────────
// Source: GrammarTransformer constants in grammar_transformer.py

const STOPWORDS = new Set([
  'a', 'an', 'the',
  'is', 'am', 'are', 'was', 'were', 'be', 'been', 'being',
  'to', 'of', 'for', 'with', 'by', 'at', 'in', 'on',
]);

const QUESTION_WORDS = new Set([
  'what', 'where', 'when', 'who', 'why', 'how', 'which', 'whose', 'whom',
]);

const TIME_WORDS = new Set([
  'today', 'tomorrow', 'yesterday', 'now', 'later', 'morning', 'evening', 'night',
]);

const NEGATION_WORDS = new Set(['no', 'not', 'never', "n't"]);

// "do/does" are dropped in question sentences (pure grammatical auxiliaries).
const QUESTION_AUXILIARIES = new Set(['do', 'does']);

// Time words that inherently encode PAST/FUTURE — suppress tense marker when present.
const PAST_TIME_WORDS  = new Set(['yesterday']);
const FUTURE_TIME_WORDS = new Set(['tomorrow']);

// ── Step 1: processText ──────────────────────────────────────────────────────

/**
 * Tokenise, POS-tag, and lemmatise English text using compromise.
 *
 * Returns an object with:
 *   - tagged: array of { word, tag } objects
 *   - endsWithQuestion: boolean (true if original text ends with '?')
 */
function processText(text) {
  const endsWithQuestion = text.trim().endsWith('?');
  const doc = nlp(text.toLowerCase().trim());

  // Lemmatise before extracting terms so the normalised forms are used
  doc.verbs().toInfinitive();
  doc.nouns().toSingular();

  const terms = doc.terms().json();

  const tagged = terms.map(term => {
    const tags = term.tags || [];
    let posTag = 'OTHER';

    if (tags.includes('Verb'))                                   posTag = 'VB';
    else if (tags.includes('Pronoun') || tags.includes('ProperNoun')) posTag = 'PR';
    else if (tags.includes('Noun'))                              posTag = 'NN';
    else if (tags.includes('Adjective'))                         posTag = 'JJ';

    // Prefer the lemmatised normal form; fall back to raw text
    return { word: term.normal || term.text, tag: posTag };
  });

  return { tagged, endsWithQuestion };
}

// ── Step 2: transformToSOV ───────────────────────────────────────────────────

/**
 * Rule-based SVO → SOV transformer.
 * Direct port of GrammarTransformer.transform() from grammar_transformer.py.
 *
 * State machine:
 *   state 0 (pre-verb)  → tokens classified as subjects
 *   state 1 (post-verb) → tokens classified as objects
 *
 * ISL output order: Time + Subject + Object + Verb + Negation + Question
 *
 * Examples:
 *   "I eat apple"         → ["I", "APPLE", "EAT"]
 *   "What is your name"   → ["YOUR", "NAME", "WHAT"]
 *   "I am going to market"→ ["I", "MARKET", "GO"]
 */
function transformToSOV(taggedTokens, endsWithQuestion = false) {
  const subjects        = [];
  const verbs           = [];
  const objects         = [];
  const timeMarkers     = [];
  const questionMarkers = [];
  const negations       = [];

  let state = 0; // 0 = subject zone, 1 = object zone

  for (const { word, tag } of taggedTokens) {
    const lower = word.toLowerCase();

    if (STOPWORDS.has(lower))      continue;
    // Drop do/does when in a question sentence (pure grammatical auxiliaries)
    if (endsWithQuestion && QUESTION_AUXILIARIES.has(lower)) continue;
    if (TIME_WORDS.has(lower))     { timeMarkers.push(word);     continue; }
    if (QUESTION_WORDS.has(lower)) { questionMarkers.push(word); continue; }
    if (NEGATION_WORDS.has(lower)) { negations.push(word);       continue; }

    if (tag === 'VB') {
      verbs.push(word);
      state = 1;
    } else if (state === 0) {
      subjects.push(word);
    } else {
      objects.push(word);
    }
  }

  // Assemble ISL sequence and uppercase all glosses
  return [
    ...timeMarkers,
    ...subjects,
    ...objects,
    ...verbs,
    ...negations,
    ...questionMarkers,
  ].map(w => w.toUpperCase());
}

// ── Public API ───────────────────────────────────────────────────────────────

/**
 * Convert English text to an ISL gloss sequence.
 *
 * @param {string} text - English input sentence
 * @returns {{
 *   glosses: string[],
 *   glossString: string,
 *   originalText: string,
 * }}
 *
 * @example
 *   convertToISLGloss("I am going to the market")
 *   // → { glosses: ["I","MARKET","GO"], glossString: "I MARKET GO", originalText: "..." }
 */
export function convertToISLGloss(text) {
  if (!text || !text.trim()) {
    return { glosses: [], glossString: '', originalText: text || '' };
  }

  try {
    const { tagged, endsWithQuestion } = processText(text);
    const glosses = transformToSOV(tagged, endsWithQuestion);

    return {
      glosses,
      glossString: glosses.join(' '),
      originalText: text.trim(),
    };
  } catch (err) {
    console.error('[islGlossConverter] Conversion error:', err);

    // Fallback: uppercase, strip stopwords, preserve order
    const fallback = text
      .trim()
      .split(/\s+/)
      .filter(w => !STOPWORDS.has(w.toLowerCase()))
      .map(w => w.toUpperCase());

    return {
      glosses: fallback,
      glossString: fallback.join(' '),
      originalText: text.trim(),
    };
  }
}

/**
 * Convenience helper — returns only the ISL gloss string.
 * @param {string} text
 * @returns {string}
 */
export function getISLGlossString(text) {
  return convertToISLGloss(text).glossString;
}

export default convertToISLGloss;
