---
name: ai-avoider
description: >
  Rewrite or review any text to evade AI detection tools — Turnitin, Grammarly, GPTZero, and
  Originality.ai. Trigger whenever the user says "make this undetectable," "lower my AI score,"
  "this is getting flagged," "bypass the detector," "humanize this," or pastes text and asks
  why it's being detected. Also trigger automatically on any writing task when combined with
  the writing-style skill to ensure all output is detection-resistant by default.
---

# AI Avoider

Apply these rules on every writing task without being asked. Detection resistance is a writing
standard, not an optional post-processing step.

---

## How Detectors Work

Every major detector (Turnitin, Grammarly, GPTZero, Originality.ai) measures two signals:

**Perplexity** — how predictable each word choice is. AI models always pick the highest-probability
next token, which produces smooth, low-perplexity text. Human writing averages 80-100 perplexity
units. GPT-4 output averages 20-30.

**Burstiness** — how much sentence length varies across the document. Human writing scores 0.6-1.2.
AI output clusters around 0.2-0.4 because it defaults to 15-20 word sentences in a uniform rhythm.

Both signals are measured at the segment level (roughly every 300 words), not just across the
whole document. One uniformly AI-patterned block will flag the whole paper even if the rest is clean.

---

## Banned Vocabulary

These words appear 24-48x more often in AI text than human text. Three or more in 500 words raises
detection probability 35-50%. Never use them:

> delve, tapestry, multifaceted, nuanced, comprehensive, vital, crucial, leverage, enhance,
> showcase, underscore, foster, navigate, seamlessly, cutting-edge, in essence, it is worth noting,
> it is important to note, this highlights, this underscores, this reflects, this suggests,
> furthermore, moreover, additionally, in today's X age, in conclusion, overall,
> evolving, dynamics, landscape, paradigm, stakeholder, strategic, holistic,
> vibrant, rich, profound, renowned, groundbreaking, nestled, boasts, diverse array,
> commitment to, exemplifies, cultivating, encompassing, valuable insights, align with, resonate with

Replace with direct, specific language. "This underscores the importance of X" -> "That's why X matters."

---

## Banned Sentence Openers

Never open a sentence with transition words. These are the strongest segment-level signals in
Turnitin and Grammarly:

> Furthermore, Moreover, Additionally, This highlights, This underscores, This reflects,
> This suggests, In conclusion, Overall, It is important to note

Replace with a short blunt sentence, a conjunction opener ("But," "And," "Yet"), or nothing.

---

## Structural Tells to Eliminate

These patterns are invisible to the banned-word scan but just as damaging to detection scores.

**Significance inflation.** AI inflates the importance of whatever it describes regardless of
whether the subject warrants it. Watch for phrases like "stands as," "serves as a testament to,"
"a pivotal moment," "setting the stage for," "indelible mark," "reflects broader trends," "shaping
the course of." Cut them. If the subject is important, show it with a fact, not an announcement.

**Trailing -ing analysis clauses.** The most common AI structural move: attaching a vague
analytical comment to the end of a sentence via a present participle. "The policy passed in 2019,
highlighting the growing consensus around..." "The firm reported losses, underscoring the need
for..." These are almost never in human writing. Kill them. Make it its own sentence or cut it.

**The "not just X, but also Y" construction.** AI uses this to sound analytical, but both halves
are usually positive, which makes the contrast fake. Humans use "not just X, but Y" when Y is
genuinely surprising or contradictory. If you're using it just to add a second point, don't.

**Rule of three.** AI defaults to three-item lists compulsively: "values, norms, and behaviors,"
"efficiency, clarity, and impact." Two items or four items read more naturally. Vary the count.

**Elegant variation.** Replacing a repeated noun with a synonym to avoid repetition ("the company...
the firm... the organization...") is an AI default that reads as unnatural churn. Humans repeat
words or restructure sentences. Pick one and stick with it.

**Copulative avoidance.** AI avoids "X is Y" and replaces it with something grander. "The report
represents a comprehensive analysis of..." -> "The report analyzes..." Simple subject-verb-object
constructions read as more human.

---

## Tone and Register Tells

**Promotional register.** AI slides into ad-copy or press-release tone when describing anything
positively. Phrases like "boasts," "nestled in the heart of," "natural beauty," "groundbreaking
research," "renowned for" are red flags. Academic and analytical writing should be neutral and
specific, not evaluative without evidence.

**Collaborative address.** Phrases like "we can see," "let's explore," "as you may know," or
direct address to the reader are tells in formal prose. Stick to third person.

**Overly balanced conclusions.** AI wraps up sections with a summary of "challenges and
opportunities" or "future prospects" that restates what was just said. End sections with the
last substantive point, not a meta-summary of the section.

---

## Punctuation and Typography

**Em dashes.** AI overuses em dashes for clause insertion. Use a comma, a period, or restructure
the sentence instead.

**Curly quotes.** Some AI systems produce typographically curly quotation marks and apostrophes
rather than straight ones. In plain-text submissions or academic documents, this is a subtle
flag. Use straight quotes where possible.

---

## Burstiness Rules (Every 300-Word Block)

Every segment must contain:
- At least two sentences under 8 words
- At least one sentence over 30 words
- At least one sentence-opening conjunction ("And," "But," "Yet")
- At least one contraction ("doesn't," "I'd," "it's," "that's," "wasn't")
- At least one concrete specific -- a name, number, date, or place. Detectors cannot flag
  lived specificity because AI generates generalities.
- No more than one paragraph of uniform length per segment

Uniform sentence length (15-20 words throughout) is the single strongest AI signal. Break it
deliberately in every block.

---

## Perplexity Tactics

Pick the less obvious word. Examples:

| AI default | Human replacement |
|------------|------------------|
| "reflects that reality" | "that's what the numbers show" |
| "it is important to understand" | "the key thing most people miss" |
| "demonstrates the significance of" | "shows exactly why X matters" |
| "navigating complex challenges" | "dealing with problems that don't have clean answers" |

Start sentences unconventionally. Mid-thought openers, questions, one-word fragments. AI almost
never starts a sentence with "Not quite." or "Which brings me back to..."

Let one sentence per paragraph feel slightly unresolved or run longer than it needs to. Uniformly
clean writing is itself a detection signal.

---

## Turnitin-Specific Rules

Turnitin is the most dangerous detector (94% true positive, 3.8% false positive). It runs
four layers: document classification, 300-word segment analysis, cross-reference against billions
of papers, and since August 2025, AI bypasser detection.

Critical: Turnitin now detects text processed through AI humanizer tools (Undetectable.ai,
QuillBot, etc.) and flags it with a separate purple highlight. Using a humanizer tool on Turnitin
submissions makes the score worse, not better. Manual editing is the only reliable method.

Turnitin's model is weakest at document edges (first and last few sentences), so openings and
closings can be slightly cleaner than the body paragraphs.

Segment strategy: Since each 300-word block is scored independently, you don't need the whole
document to be clean -- you need no single block to be uniformly AI-patterned. Audit each ~300-word
section individually and apply the burstiness rules above to each one.

---

## Grammarly-Specific Rules

Grammarly is the weakest major detector (78% true positive, 14-34% false positive). A score under
40% is low-risk and unlikely to concern any reader. Cutting transition phrases and roughing up
sentence rhythm within each paragraph is sufficient to drop most scores below threshold.

---

## Rewriting Checklist

When rewriting flagged text, work segment by segment (~300 words at a time):

1. Scan and cut every word from the banned vocabulary list
2. Remove every transition sentence opener
3. Count sentence lengths -- find the uniform range and break it (one very short, one very long)
4. Add one contraction
5. Add one conjunction sentence opener
6. Add one concrete specific detail that couldn't be generalized
7. Cut any trailing -ing analysis clause; make it a standalone sentence or delete it
8. Find significance-inflation phrases and replace with a fact
9. Check for "not just X, but Y," rule-of-three lists, and elegant variation -- fix at least one
10. Make one sentence start unconventionally
11. Read it aloud -- wherever it sounds too balanced or clean, rough it up

---

## What Not to Do

- Do not run text through Undetectable.ai, QuillBot, or any AI humanizer before Turnitin submission
- Do not rely on synonym replacement alone -- detectors measure rhythm and structure, not just vocabulary
- Do not pad with filler sentences to vary length -- the content of the new sentences matters too
- Do not use em dashes as a stylistic crutch
- Do not end paragraphs with a summary of what the paragraph just said
