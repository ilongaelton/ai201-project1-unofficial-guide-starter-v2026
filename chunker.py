"""
Stage 2 of the pipeline: splitting documents into chunks.

⚠️ THIS IS THE FILE YOU CHANGE IN MILESTONE 3.

`split_documents` below is deliberately plain. It cuts every document into
fixed-size pieces with a fixed overlap and pays no attention to where sentences
or paragraphs end. It works, and it is not good.

On a corpus of short posts it may not cut anything at all: `campus_life` comes
out as 88 documents and 88 chunks, because almost nothing in it reaches 800
characters. That is the baseline, not a bug — Milestone 3 is where you decide
whether one post should stay one chunk.

Your job in Milestone 3 is to replace the *body* of `split_documents` with a
strategy that fits the documents you actually read in Milestone 1. Keep the
name and the shape of what it returns — the rest of the pipeline calls it, and
your README has to name the function that produced your chunks.

If you get stuck for 30 minutes, `fallback_split` is the original. Switch back
to it, write down what you saw, and move on. That's a real observation about
your pipeline, not giving up.
"""

import re
from dataclasses import dataclass

import config
from ingest import Document

# Below this, a chunk is a fragment rather than a thought. Criterion 4.
MIN_CHUNK = 150


@dataclass
class Chunk:
    """One piece of one document."""

    text: str
    source: str        # which file it came from
    index: int         # which chunk within that file, starting at 0
    produced_by: str   # the function that made it — cite this in your README

    @property
    def label(self) -> str:
        return f"{self.source}#{self.index}"


def fallback_split(
    documents: list[Document],
    chunk_size: int | None = None,
    overlap: int | None = None,
) -> list[Chunk]:
    """
    The starter's original chunker. Fixed-size character windows with overlap.

    Keep this function. Milestone 3's stop rule points back at it, and having
    something to compare your own strategy against is useful in unit 2.
    """
    chunk_size = chunk_size or config.CHUNK_SIZE
    overlap = overlap or config.CHUNK_OVERLAP

    if overlap >= chunk_size:
        raise ValueError("overlap has to be smaller than chunk_size")

    chunks: list[Chunk] = []
    for doc in documents:
        start = 0
        index = 0
        while start < len(doc.text):
            piece = doc.text[start : start + chunk_size].strip()
            if piece:
                chunks.append(
                    Chunk(
                        text=piece,
                        source=doc.source,
                        index=index,
                        produced_by="chunker.py::fallback_split",
                    )
                )
                index += 1
            start += chunk_size - overlap

    return chunks


def _sections(text: str) -> tuple[str, list[tuple[str, str]]]:
    """Break one document into (title, [(heading, body), ...]).

    My corpus is `city_guides`: fourteen travel guides, each one a `# Town`
    title followed by `## Getting there`, `## Eat and drink`, `## When to go`.
    The author already decided where one thought ends and the next begins, and
    those decisions are sitting right there in the markup.

    Anything before the first `##` — the title, and the paragraph of overview
    most guides open with — comes back as a section with an empty heading, so
    it is kept rather than dropped.
    """
    lines = text.split("\n")
    title = ""
    if lines and lines[0].startswith("# "):
        title = lines[0].strip()
        lines = lines[1:]

    sections: list[tuple[str, str]] = []
    for part in re.split(r"\n(?=##\s)", "\n".join(lines)):
        part = part.strip()
        if not part:
            continue
        if part.startswith("##"):
            heading, _, body = part.partition("\n")
            sections.append((heading.strip(), body.strip()))
        else:
            sections.append(("", part))
    return title, sections


def _pack(prefix: str, body: str, budget: int) -> list[str]:
    """Fit one section into as few chunks as possible, splitting on paragraphs.

    `prefix` is the heading context — "# Kestrelford" plus "## Eat and drink" —
    and it is repeated at the top of every piece a long section turns into, so
    no chunk can end up saying "the pubs serve 12 to 2" without saying where.

    Nothing in `city_guides` actually needs this: the longest section is 712
    characters and the budget is 800. It is here so that a corpus with longer
    sections degrades into paragraph-sized chunks instead of one enormous one.
    """
    room = max(budget - len(prefix) - 2, 200)
    pieces, current = [], ""

    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if current and len(current) + len(paragraph) + 2 > room:
            pieces.append(current)
            current = paragraph
        else:
            current = f"{current}\n\n{paragraph}" if current else paragraph
    if current:
        pieces.append(current)

    return [f"{prefix}\n\n{piece}".strip() if prefix else piece for piece in pieces]


def _merge_short(pieces: list[str], budget: int) -> list[str]:
    """Fold anything under MIN_CHUNK into its neighbour.

    Four of my documents open with a title line of 24 to 28 characters, and
    splitting on headings alone would emit "# Eating across the region" as a
    chunk of its own — retrievable, and useless. This is criterion 4's floor.
    """
    merged: list[str] = []
    for piece in pieces:
        if merged and len(piece) < MIN_CHUNK and len(merged[-1]) + len(piece) + 2 <= budget:
            merged[-1] = f"{merged[-1]}\n\n{piece}"
        else:
            merged.append(piece)

    # A short first piece has no neighbour behind it to merge into.
    if len(merged) > 1 and len(merged[0]) < MIN_CHUNK:
        if len(merged[0]) + len(merged[1]) + 2 <= budget:
            merged[1] = f"{merged[0]}\n\n{merged[1]}"
            merged.pop(0)
    return merged


def split_documents(documents: list[Document]) -> list[Chunk]:
    """
    Split documents at their section headings rather than at a character count.

    Milestone 3. The starter's `fallback_split` cuts every 800 characters and
    pays no attention to the documents: on `city_guides` it produced 51 chunks
    of which exactly one both started at a boundary and ended on a finished
    sentence, six were under 150 characters, and the shortest was 24 — the
    string "d Sundays and after 5pm.", which begins mid-word and names nothing.

    What I changed, and why each part earns its place:

      1. Split at `##` headings. My documents are travel guides and the author
         already marked where each thought ends.
      2. Repeat the title and heading at the top of every chunk. A chunk about
         pub hours that never says "Kestrelford" cannot be retrieved by a
         question that says "Kestrelford", and the section bodies genuinely do
         not repeat the town name.
      3. Enforce a 150-character floor, because splitting on headings alone
         turns four title lines into chunks with no content under them.

    A document with no `##` headings — any of the other corpora — comes out as
    one chunk per document if it fits, or paragraph-packed chunks if it does
    not, so this stays honest on material it was not designed for.
    """
    budget = config.CHUNK_SIZE
    chunks: list[Chunk] = []

    for doc in documents:
        title, sections = _sections(doc.text)

        pieces: list[str] = []
        for heading, body in sections:
            prefix = "\n".join(p for p in (title, heading) if p)
            pieces.extend(_pack(prefix, body, budget))

        for index, text in enumerate(_merge_short(pieces, budget)):
            chunks.append(
                Chunk(
                    text=text,
                    source=doc.source,
                    index=index,
                    produced_by="chunker.py::split_documents",
                )
            )

    return chunks


def describe(chunks: list[Chunk]) -> str:
    """A one-line summary, printed after indexing."""
    if not chunks:
        return "0 chunks"
    lengths = [len(c.text) for c in chunks]
    return (
        f"{len(chunks)} chunks, "
        f"{sum(lengths) // len(lengths)} characters on average "
        f"(shortest {min(lengths)}, longest {max(lengths)}), "
        f"produced by {chunks[0].produced_by}"
    )


if __name__ == "__main__":
    from ingest import load_documents

    chunks = split_documents(load_documents())
    print(describe(chunks))
