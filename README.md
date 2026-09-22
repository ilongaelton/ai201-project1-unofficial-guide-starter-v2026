# The Unofficial Guide

Haylton Ilonga — corpus: `city_guides`

---

# Unit 1

## What This Does

This is a question-answering system over `city_guides`: fourteen travel guides
covering nine towns in one region, plus five guides that cut across all of them
on eating, walking, regional transport, seasons and accessibility. You ask it a
practical question about visiting somewhere — when the pubs serve food, how
early you need to arrive to park, which towns are hard going with limited
mobility — and it finds the relevant passage, answers from it, and names the
file the answer came from.

It only answers from those fourteen documents. A question the guides do not
cover is refused before it ever reaches the model, by comparing how far the
closest retrieved passage is from the question against a fixed cutoff.

## Chunking Strategy

**Chunk size:** 800 characters, used as a ceiling rather than a target. Actual
chunks average 321 characters; the longest is 761.
**Overlap:** none.

Both of those are departures from the starter's defaults, and the reason is the
same for both: my documents come pre-divided. Each guide is a `# Town` title
over labelled sections — `## Getting there`, `## Eat and drink`, `## When to
go`. The author already decided where one thought ends and the next begins, so
I split on those headings instead of on a character count. A section boundary
is a real boundary; character 800 is not. Once chunks end where sections end,
overlap has nothing to do — it exists to stop a fixed-size cutter from slicing
a sentence in half, and there is no longer a cutter.

I checked the target was reachable before committing to it. The corpus has 98
`##` sections, the longest is 712 characters and the median is 286, so every
section fits inside the 800 ceiling whole. 800 stays as the ceiling for the
case a section is longer than that, where `_pack` falls back to splitting on
paragraph breaks.

**What I changed my mind about.** My first version split on headings and
nothing else, and it was worse in two ways I did not predict.

It emitted four chunks that were nothing but a document title — 24 to 28
characters, no content under them, because four of my guides open with a title
line before their first `##`. So `_merge_short` folds anything under 150
characters into its neighbour.

The second was the more interesting one. Section bodies never repeat the town
name: the "Eat and drink" section of `guide_kestrelford.md` says "the pubs
serve food between 12 and 2" and never says Kestrelford. A chunk of that on its
own cannot be retrieved by a question that says Kestrelford. So every chunk now
carries its title and heading at the top. That one change moved my first test
question from 0.347 to 0.180 and changed which document it retrieves — from
`guide_eating.md`, the regional summary, to `guide_kestrelford.md`, the actual
town guide.

Measured on `city_guides`, `fallback_split` → `split_documents`:

| | before | after |
|---|---|---|
| chunks | 51 | 94 |
| start at a boundary and end on a finished sentence | 1 of 51 | 94 of 94 |
| shortest chunk | 24 chars | 174 chars |
| chunks under 150 characters | 6 | 0 |

The 24-character chunk was the string `d Sundays and after 5pm.` — it begins
mid-word, names nothing, and retrieval could return it.

## Sample Chunks

Printed by `python app.py chunks -n 5`.

**Chunk 1** — source: `guide_accessibility.md#0` — produced by: `chunker.py::split_documents`

```
# Getting around the region with limited mobility

An honest assessment rather than a promotional one. Some of these places are
difficult and it is better to know in advance.
```

**Chunk 2** — source: `guide_corry_vale.md#5` — produced by: `chunker.py::split_documents`

```
# Corry Vale
## Where to stay

Perhaps thirty beds in the entire valley, spread across two pubs and a handful of farmhouse rooms. In summer these are booked months ahead. Camping is permitted on two marked fields and nowhere else.
```

**Chunk 3** — source: `guide_givens_mill.md#2` — produced by: `chunker.py::split_documents`

```
# Givens Mill
## Getting around

Everything is on one street along the river. The mill is at one end and the church at the other, eight minutes apart. The riverside path continues in both directions for as far as you want to walk.
```

**Chunk 4** — source: `guide_kestrelford.md#4` — produced by: `chunker.py::split_documents`

```
# Kestrelford
## What to see

The market square on a Saturday morning is the main event and has run continuously since the 1400s. The parish church has a 13th-century tower you can climb for £2. The old trackbed walk runs six miles to the next village along an easy gradient and is the best half-day here.
```

**Chunk 5** — source: `guide_pellew_sands.md#6` — produced by: `chunker.py::split_documents`

```
# Pellew Sands
## When to go

June and September for the beach without the crowds. July and August are busy and the town is at its most itself, for better and worse. Winter is bleak, largely closed, and has a following among people who like that sort of thing.
```

Chunk 1 is the one that fails the test the tool asks you to apply — it is a
title and a framing sentence, and nobody can answer a question from it. It
survives because it is 174 characters, over my floor. The other four each hold
one complete section and say which town they are about.

## Sample Answer

<!-- TODO: run `python app.py ask "..."` once the API key is in .env and paste
     the real output here, with the source line visible. -->

**Question:**

**Answer:**

```
```

**My relevance cutoff:**

<!-- TODO: the number you settle on, and the sentence explaining how you got
     there from the two groups below. -->

I ran my five questions and the five in `OUT_OF_SCOPE` through
`python app.py retrieve` and recorded the best distance for each. The two
groups do not overlap and there is nothing at all between 0.542 and 0.803.

| Question | In corpus? | Best distance |
|---|---|---|
| What time do the pubs in Kestrelford serve food? | yes | 0.180 |
| How early do I need to arrive at Halden Bay to park on a summer weekend? | yes | 0.282 |
| How much does it cost to climb the church tower in Kestrelford? | yes | 0.439 |
| Where can I get dinner on a Sunday evening in this region? | yes | 0.499 |
| Which towns are difficult to get around with limited mobility? | yes | 0.542 |
| What is the capital of Mongolia? | no | 0.803 |
| What is the recommended dosage of ibuprofen for a headache? | no | 0.835 |
| How do I write a for loop in Rust? | no | 0.836 |
| How do I change the oil in a diesel engine? | no | 0.888 |
| Who won the 1994 World Cup? | no | 0.975 |

Worst in-corpus question: 0.542. Best out-of-corpus question: 0.803. The gap is
0.260 wide and its midpoint is 0.673.

These are the numbers after the Milestone 3 re-chunk. I measured once before it
as well, and the whole in-corpus group moved: 0.347/0.447/0.559/0.356/0.562
became 0.180/0.499/0.542/0.282/0.439. Four of five improved, one got slightly
worse. That is the reason a cutoff has to be measured against the chunking it
will actually run on.

## How I Used AI

<!-- TODO: these are drafted from what actually happened — check them, and put
     them in your own words before submitting. -->

**1.** I asked Claude to draft five test questions from the corpus. What came
back was five questions with the phrase a correct answer would have to contain,
each traced to a specific file. I kept the set but I would not have thought to
check them before writing the criteria — it ran all five through retrieval
first and showed me that every one already returned a chunk containing the
expected phrase, which is what let me write criterion 1 as a prediction about
which single question I expected to lose rather than as a guess.

**2.** I asked it to justify why criterion 4's target was 4 of 5 and not 5 of
5, and the first answer it gave was that some sections in my corpus are too
long to keep whole. That was wrong. When it checked, the longest section is 712
characters against an 800 ceiling and nothing exceeds it — the opposite of the
claim. The real constraint was at the other end: four documents open with a
24-to-28 character title line that a heading splitter would emit as its own
chunk. That is where the 150-character floor came from, and it is in
`criteria.md` because the first explanation did not survive being checked.

<!-- ── Stretch features ─────────────────────────────────────────────────────
     Doing one? Say so here BEFORE you start. A feature this README never
     claims earns nothing.
     ───────────────────────────────────────────────────────────────────────── -->

---

# Unit 2

<!-- These sections get ADDED to what's already above. Don't delete or rewrite
     unit 1 — the point is that someone can see what you said before you knew
     how it went. -->

## Run Log — Before

<!-- Your five criteria, three runs each. `python run_eval.py --label before`
     runs the questions, puts the OUT_OF_SCOPE ones through the gate, and
     writes it all into results/ for you. Targets come from criteria.md; the
     verdict column is your call.

     Criterion 3 is measured in one deterministic pass rather than three, so
     the same number goes in all three run columns. That's correct, not lazy.

     Milestone 1. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks stop where the documents stop | 4 of 5 |  |  |  |  |
| 5. Named source is the source the fact came from | 4 of 5 |  |  |  |  |

<!-- Underneath, paste the REAL output for each criterion from one of your
     runs — the actual text your system produced, not a description of it.
     Name the file and function that produced it. -->

## Verdicts

<!-- MET or MISSED for each of the five, against the target you wrote last
     unit — not a new one. Plus a sentence on how you decided. That sentence
     matters most where it was close.

     If your target said 4 of 5 and your runs came out 4, 3, 4, that's a MISS.
     The target has to hold, not show up occasionally.

     Milestone 2. -->

| # | Criterion | Verdict | How I decided |
|---|---|---|---|
| 1 |  |  |  |
| 2 |  |  |  |
| 3 |  |  |  |
| 4 |  |  |  |
| 5 |  |  |  |

## Diagnoses

<!-- For each miss: which stage caused it, and how. The stage alone isn't
     enough — you need the mechanism.

     Not a diagnosis: "Question 3 didn't work."
     A diagnosis:     "Question 3 asks about laundry costs. The answer is in
                       one sentence that got split across two chunks, so
                       neither chunk on its own contains it."

     The five stages: loading → chunking → embedding → retrieval → generation.

     Look for a pattern. If three misses all ask about numbers, that's one
     problem, not three.

     Missed nothing? Say so, then say honestly whether your targets were set
     low, and which one you'd tighten and to what.

     Milestone 3. -->

## The Improvement

**What I changed:**

**Why I picked it:**

<!-- Connect it to a specific diagnosis above in one sentence. If you can't,
     you picked a fix because it sounded impressive. -->

### Run Log — After

<!-- Same format, same five criteria, three runs each.
     `python run_eval.py --label after` -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 |  |  |  |  |
| 4. Chunks stop where the documents stop | 4 of 5 |  |  |  |  |
| 5. Named source is the source the fact came from | 4 of 5 |  |  |  |  |

**Did it help?**

<!-- Say plainly whether it did, and how you know. If it made things worse,
     say that — a change that backfired, honestly reported, earns full credit
     and is more interesting than one that worked. What matters is that you can
     tell.

     Milestone 4. -->

## What's Still Broken

<!-- For each criterion still missed after your fix: what you'd do about it,
     and why you stopped where you did.

     "I ran out of time" is fine if it's true. Pretending nothing is left is
     not.

     Milestone 5. -->

## What I'd Do Differently

<!-- Knowing what you know now — which of your five criteria would you write
     differently, and why?

     Milestone 5. -->
