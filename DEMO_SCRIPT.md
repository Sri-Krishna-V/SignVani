# SignVani — 3-Minute Demo Script

> `[ACTION]` = what you do on screen | plain text = what you say out loud  
> Setup: run `start-signvani.bat`, open `http://localhost:3000/sign-kit/home`

---

## [0:00 – 0:20] Opening

`[ACTION → Home page]`

"India has over five million people with hearing impairments who rely on Indian Sign Language every day — yet most software still can't bridge that gap.

SignVani converts spoken and written English into animated ISL gestures on a live 3-D avatar. No app, no hardware. Let me show you."

---

## [0:20 – 1:10] Text to ISL

`[ACTION → navigate to Convert page, ISL Grammar (SOV) toggle ON]`

**Simple reorder**
`[ACTION → type "I eat food" → Start Animations]`
"English is Subject–Verb–Object. ISL is Subject–Object–Verb. The backend rewrites it: **I FOOD EAT** — the avatar signs exactly that."

**Past tense**
`[ACTION → type "She went to school yesterday" → Start Animations]`
"Time words move to the front in ISL. Past tense gets a marker at the end. Result: **YESTERDAY SHE SCHOOL GO PAST** — see the purple badge."

**Negation**
`[ACTION → type "I do not know" → Start Animations]`
"Negation always goes last in ISL. **I KNOW NOT.** Red badge — NEGATED."

**Question**
`[ACTION → type "Where do you live?" → Start Animations]`
"WH-words move to the end. **YOU LIVE WHERE.** Green badge — WH-question."

---

## [1:10 – 1:30] Speech to ISL

`[ACTION → Mic On → say "I am not hungry" → Mic Off → Start Animations]`

"Real-time voice input, no extra hardware. Same pipeline. Result: **I HUNGRY NOT** — negation last, grammar corrected automatically."

---

## [1:30 – 2:00] Learn ISL

`[ACTION → navigate to Learn ISL]`

`[ACTION → Alphabets tab → press S, I, G on keyboard]`
"Every letter is fingerspelled. Press any key — the avatar signs it instantly."

`[ACTION → Categories tab → click Emotions → click HAPPY, SAD, ANGRY]`
"Ten categories, 48 common words. Watch the handshapes change."

`[ACTION → switch to Beginner preset]`
"Beginner mode slows everything down so learners can follow each ha  ndshape clearly."

---

## [2:00 – 2:30] Create & Share Videos

`[ACTION → navigate to Create Video]`
`[ACTION → fill Title: "Morning Greeting", Created By: "Demo" → Speech input → say "Good morning, how are you?" → Create]`

"Save any signing sequence as a shareable video with a unique link — public or private. A teacher builds a lesson library. A parent sends a greeting. A student reviews before an exam."

---

## [2:30 – 2:45] Video Gallery

`[ACTION → navigate to Videos Gallery → click any video]`

"Every saved video lives here. Anyone with the link can replay it — no account, no backend needed."

---

## [2:45 – 3:00] Closing

"User study — 25 participants:
4.44 out of 5 satisfaction. 81.5 SUS usability score. 6.4% speech error rate.

React, Three.js, FastAPI, NLTK — running locally, offline-capable.

That's SignVani — giving Indian Sign Language a voice."
