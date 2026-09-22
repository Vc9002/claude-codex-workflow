---
name: imagegen-extras
description: Delta guidance for the system `imagegen` skill (non-editable, `.system`-owned) — semantic validation of generated educational/scientific diagrams before delivery. Load alongside `imagegen` whenever the image being generated depicts a mathematical, scientific, or otherwise checkable relationship (graphs, diagrams, charts with a "correct answer").
---

# imagegen — educational/scientific diagram validation addendum (internal)

Internal note. The system `imagegen` skill handles generation mechanics
(tool selection, save paths, transparency) but doesn't validate whether a
generated image is *correct* — only whether it was produced. This file is
that addendum: load it alongside `imagegen` whenever the requested image
depicts a checkable mathematical or scientific relationship (a function
graph, a labeled diagram, a shifted/transformed curve, a sign-of-derivative
chart), as opposed to purely aesthetic or illustrative art.

## The rule

Visual plausibility and correct-looking labels do not guarantee semantic
correctness. Two generated diagrams looked polished and well-labeled while
directly contradicting the math they were meant to illustrate: a
marginal-cost graph placed its curves opposite what its own derivative-sign
labels claimed, and a shifted trigonometric graph kept the *unshifted*
landmark points (peaks/zeros in their original, pre-shift positions).

**Before delivering a generated instructional diagram:**
1. Extract a small, explicit list of mathematical invariants the image must
   satisfy *before* prompting — curve ordering, signs, extrema locations,
   shift/translation direction, endpoints, isolated/marked points, units.
2. After generation, inspect the output against every invariant on that
   list individually — don't rely on a holistic "does this look right"
   read.
3. Reject and regenerate if any invariant fails, even if the image is
   otherwise attractive and well-labeled. A good-looking wrong diagram is
   worse than no diagram — it actively misleads.

## Why

Image generation models optimize for visual plausibility, not mathematical
consistency between labels and the picture. A graph can have correctly
formatted axis labels, a correctly styled curve, and a caption that states
the right derivative sign — while the actual curve drawn violates that
sign. Nothing in the generation pipeline checks this; only an explicit
post-generation comparison against the source math does.

## Checklist

1. Before prompting, write down the invariants (as a short list, not prose)
   that the finished image must satisfy.
2. After the image renders, check each invariant against the actual pixels
   — not the prompt, not the caption.
3. Treat "looks like a textbook diagram" as necessary but not sufficient.
4. On any invariant failure, regenerate rather than patching the caption to
   match the (wrong) image.
