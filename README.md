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

**My relevance cutoff: 0.70**, set in `config.py`.

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

**Why 0.70 and not the midpoint.** Any number between 0.543 and 0.802 refuses
all five out-of-corpus questions and passes all five real ones, so the
measurement alone does not pick one — I had to decide what I would rather get
wrong. 0.70 leaves 0.158 of headroom above my worst real question and 0.103
below the nearest out-of-corpus one, so it is biased toward letting questions
through rather than refusing them.

That is on purpose, and it is because refusing is not the only defence this
system has. The gate is the first layer; `generate.py`'s grounding instruction
is the second, and it tells the model to say it doesn't have enough information
when the documents don't cover the question. A question that slips past the
gate still has to get past that. A real question that the gate wrongly refuses
gets nothing — there is no second layer on that side. So I would rather the
cutoff err toward answering, and my five questions only sample a narrow slice
of the ways someone might phrase a question about these guides. The 0.542 I
measured is not a ceiling on how far a legitimate question can land.

I also started at 0.6, which is inside the gap and works, and moved it because
0.6 is only 0.058 above my worst real question while wasting 0.20 of the room
on the other side. The right number was not the default; it just happened not
to be wrong.

**One caveat I want on the record.** These are the numbers after the Milestone
3 re-chunk. I measured once before it as well, and the whole in-corpus group
moved: 0.347/0.447/0.559/0.356/0.562 became 0.180/0.499/0.542/0.282/0.439. Four
of five improved, one got slightly worse. A cutoff is only valid against the
chunking it was measured on, so if I change the chunker again in unit 2 this
number has to be re-measured rather than carried over.

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

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Retrieved chunk contains the answer | 4 of 5 |  |  |  |  |
| 2. Every answer names a source | 5 of 5 |  |  |  |  |
| 3. Gate stops out-of-corpus questions | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 4. Chunks stop where the documents stop | 4 of 5 | 5/5 | 5/5 | 5/5 | MET |
| 5. Named source is the source the fact came from | 4 of 5 |  |  |  |  |

Criteria 3 and 4 are filled in; 1, 2 and 5 are not yet, because all three
judge a generated answer and `run_eval.py` has not been run against a live
model yet.

**Criteria 3 and 4 come out identical in all three columns, and that is
correct rather than a sign I did not really re-run.** Neither one involves a
model call. Criterion 3 is retrieval, which is deterministic, compared against
a fixed cutoff. Criterion 4 is a property of the chunker, which produces the
same 94 chunks every time it runs. There is one number for each and it goes in
all three columns. Criteria 1, 2 and 5 are the ones that can move between runs,
because those are the ones the model participates in.

### Real output — criterion 3

Produced by `gate.py::check` on the results of `store.py::search`, cutoff 0.70,
over the five questions in `questions.py::OUT_OF_SCOPE`:

```
refused  best 0.803  What is the capital of Mongolia?
refused  best 0.835  What is the recommended dosage of ibuprofen for a headache?
refused  best 0.836  How do I write a for loop in Rust?
refused  best 0.888  How do I change the oil in a diesel engine?
refused  best 0.975  Who won the 1994 World Cup?
-> 5 of 5 refused
```

Every one is refused before it reaches the model, so criterion 3 costs no API
calls. The closest out-of-corpus question sits at 0.803 against a cutoff of
0.70 — a margin of 0.103, which is the headroom I argued for in unit 1.

### Real output — criterion 4

Produced by `chunker.py::split_documents` over the fourteen documents in
`city_guides`:

```
94 chunks; 94 start at a boundary and end on a finished sentence
shortest 174, longest 761, under 150: 0
sampled 5 by stride: 5 of 5 pass
```

The criterion asks for at least 4 of 5 sampled chunks, and sampling five by
stride the way `app.py chunks` does gives 5 of 5. The whole-corpus number is
stronger than the sample: all 94 pass, not just the five I looked at.

### Real output — criteria 1, 2 and 5

**Not measured yet.** There is no real output to paste here, and I would rather
say that than describe output I do not have.

All three of these criteria judge a generated answer, so each one needs
`generate.py::answer_from_chunks` to return something. I ran
`python run_eval.py --label before` on 2026-09-27 and it stopped on the first
question — the API key in my `.env` is still the placeholder from
`.env.example`, so the call to the model came back `400 INVALID_ARGUMENT`,
`API_KEY_INVALID`. `run_eval.py::write_report` only writes once every question
has finished, so nothing reached `results/` and there is no
`results/run_*_before.md` to quote from.

Nothing above this line is affected. Criteria 3 and 4 were measured without a
model — criterion 3 is refused at the gate before any call is made, and
criterion 4 is a property of the chunker — which is why those two have real
output and these three do not.

What this takes to finish: a valid `GEMINI_API_KEY` in `.env`, then re-run
`python run_eval.py --label before`, commit the run log it writes into
`results/`, and paste the answers for criteria 1, 2 and 5 here.

<!-- Paste the REAL output for each — the actual text the system produced, not
     a description of it. Name the file and function that produced it. -->

<!-- TODO: from results/run_*_before.md once run_eval.py has run. -->

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
