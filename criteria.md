# Acceptance criteria — The Unofficial Guide

Five criteria that say what "working" means for this system, written in unit 1
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"Retrieval works"* is an opinion. *"For at
least 4 of my 5 test questions, the top results include a chunk containing the
answer"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter or looser one. A reason that says something about your corpus or your
pipeline earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## 1. Retrieved chunks contain the answer

For at least 4 of my 5 test questions, the retrieved chunks include one that
contains the answer.

**Why this target:** Four of my five questions are answered in more than one
document — the eating and accessibility guides repeat facts the town guides
also carry — so those should be reliable. The fifth, the church tower fee, is a
single clause in the middle of `guide_kestrelford.md`, and a chunker that cuts
on character count can land a boundary in the middle of it. I expect that one
to be the one I lose, which is why the target is 4 and not 5.

---

## 2. Every answer names a source

Every answer the system produces names at least one source document.

**Why this target:** All five, because naming a source is not a judgement call
the model has to get right — `generate.py::build_prompt` labels every excerpt
`[from filename]` and the system instruction tells it to cite that filename.
The information is in the prompt every single time. For this to fail the model
would have to ignore an instruction about material sitting directly in front of
it, and if that happens even once I want the criterion to catch it rather than
average it away.

---

## 3. The relevance gate stops out-of-corpus questions

When I ask a question my documents clearly don't cover, the relevance gate
stops it and the system returns "I don't have enough information about that" —
in at least 4 of 5 tries.

<!-- The five questions are the ones in `OUT_OF_SCOPE` at the bottom of
     `questions.py`, and `run_eval.py` puts them through the gate and writes
     what happened into your run log. Swap them for your own if you'd rather —
     just keep five of them, or the "4 of 5" above has nothing to be 4 of. -->

**Why this target:** I measured both groups before setting the cutoff. My five
in-corpus questions come back at 0.347 to 0.562; the five `OUT_OF_SCOPE`
questions come back at 0.829 to 0.903. That is a clean gap of 0.267 with
nothing inside it, so at any cutoff in that range the gate refuses 5 of 5. I
am still writing 4 of 5 rather than 5 of 5, because changing the chunker in
Milestone 3 moves every distance underneath the cutoff, and a target that only
holds at today's chunk size is a target I set after seeing the answer.

---

## 4. Chunks stop where the documents stop

At least 4 of 5 sampled chunks begin at a section heading or a paragraph break
and end on a finished sentence, and no chunk is shorter than 150 characters.

**Why this target:** These numbers come from counting what the starter's
chunker actually does to my corpus, not from a guess. At 800 characters with
120 of overlap, `city_guides` produces 51 chunks, and exactly **1 of those 51**
both starts at a boundary and ends on sentence punctuation. Six are under 150
characters and the shortest is 24 — `'d Sundays and after 5pm.'`, which begins
mid-word, names nothing, and is a chunk the retriever can return.

My documents are travel guides built out of labelled sections: Getting there,
Eat and drink, When to go. A reader looking for opening hours wants the "Eat
and drink" section, and a boundary drawn at character 800 has no idea that
section exists. I checked whether the target is reachable before setting it:
the corpus has 98 `##` sections, the longest is 712 characters and the median
is 286, so a splitter that cuts on headings can keep every section whole
without exceeding the chunk size I already have.

The 150-character floor is the half that will actually bite. Four of my
documents open with a title line of 24 to 28 characters before their first
`##` heading, so a naive heading splitter emits a chunk that is nothing but
`# Eating across the region` — retrievable, and useless. The floor forces me
to merge those into the section below them.

4 of 5 rather than 5 of 5 because `app.py chunks -n 5` samples by stride
across the corpus, so which five chunks I read changes every time the chunk
count changes. One awkward chunk in a sample of five should not turn the
criterion into a coin flip on which five I happened to land on.



---

## 5. The named source is the source the fact came from

For at least 4 of my 5 test questions, the document the answer names is a
document that actually contains the fact stated. Checked by opening the named
file and looking for the claim.

**Why this target:** Criterion 2 only asks that *a* source gets named. That is
a low bar, and my corpus gives me a specific reason to think a system can clear
it while still being wrong.

Reading the documents in Milestone 1, I found that they contradict each other.
`guide_halden_bay.md` says "The nearest full hospital is in Brightwater."
`guide_accessibility.md` says "The nearest full hospital is in Marchwood." Both
are in my corpus, both will be retrieved for a question about hospitals, and
both will be sitting in the same prompt. An answer that states one of them and
cites the other passes criterion 2 and is still useless to the person asking —
it sends them to the wrong file to check, which is the one thing a citation is
for.

I am setting this at 4 of 5 rather than 5 of 5 because I have five questions
and only some of them retrieve chunks from more than one document, so on an
easy question this is nearly free. The target is really about the hard ones.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 2 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 1. Retrieved chunks contain the answer

         For at least 4 of my 5 test questions, the retrieved chunks include
         one that contains the answer.

         **Why this target:** ...

         > **Revised in unit 2:** For at least 4 of 5 questions, the top three
         > results contain the answer.
         >
         > **Why revised:** I couldn't judge "the chunks include one that
         > contains the answer" the same way twice — I scored two questions
         > differently on Monday than on Wednesday. The new version is
         > something I can actually check.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said 4 of 5 but got 2 of 5, so 2 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.

     The whole reason the originals stay visible is so someone can see what you
     said before you knew the answer.
     ───────────────────────────────────────────────────────────────────────── -->
