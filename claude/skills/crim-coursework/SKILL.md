---
name: crim-coursework
description: Use whenever helping Vincent with CRIM 1200 (Criminal Justice) coursework — R exercises, datasets (pretrial detention, court cases), codebooks, or workshop materials (EDA, first look, hypothesis testing, linear regression, Rmarkdown). Trigger on any mention of "CRIM", "criminal justice class/course", "pretrial" or "court_cases" data, exercise numbers/names from the course, or files under ~/Downloads/Criminal_Justice_Data — even if the user doesn't name this skill directly. Also trigger before organizing newly downloaded CRIM course files. This skill enforces a hard content boundary: all course-content answers (definitions, variable meanings, methodology, stats interpretation, what a question is asking) must come only from the files in the course folder — never from outside sources, general knowledge about the topic, or assumptions about what the professor "probably" means.
---

# CRIM 1200 Coursework

## Source of truth

The **only** permitted source of course content is:

```
~/Downloads/Criminal_Justice_Data/
```

Before answering any substantive question about the course, run a fresh listing —
don't rely on a remembered file list, since Vincent adds new workshops/scripts/data
over time:

```bash
find ~/Downloads/Criminal_Justice_Data -type f | sort
```

Everything relevant to the course lives here in three folders:
- `data/` — datasets (`.csv`) and their codebooks (`.txt`)
- `scripts/` — exercise templates and reference R scripts
- `workshops/` — rendered workshop HTML files (EDA, first look, hypothesis testing,
  linear regression, Rmarkdown)

If Vincent mentions downloading more class files, check whether they've landed loose
in `~/Downloads` (not yet in this folder) and sort them into the matching subfolder
(`data/`, `scripts/`, or `workshops/`) before doing anything else — see "Keeping the
folder current" below.

## The hard rule: no outside course content

When answering a question that touches course *content* — what a variable means,
what a question is asking, how to interpret a result, which method applies, what a
dataset contains, terminology, definitions, course conventions — use **only** what
is stated or directly derivable from the files in the folder above.

This means:
- **Do not** supplement from general statistics/criminology knowledge, other
  textbooks, memory of similar courses, or web search, even if it would produce a
  "better" or more complete-sounding answer.
- **Do not** guess at what a professor "probably" means if it isn't written down in
  the exercise script, codebook, or workshop file.
- If something isn't covered by the course materials, **say so explicitly** — e.g.
  "the codebook doesn't define this variable" or "none of the workshops cover this
  method" — rather than filling the gap with outside knowledge. Vincent can then
  decide whether to ask the instructor/TA.

**Narrow exception — tool mechanics, not course content:** generic R/programming
syntax help (e.g., "what does `read_csv()` do", "why is this line throwing an
error", correcting a typo in a pipe chain) is fine to explain normally, since it's
about the R language itself, not the substance of the course. If in doubt whether
something counts as "course content" vs. "tool mechanics," treat it as course
content and stick to the files.

This rule applies to setup/organizational work too (see the earlier session:
building the `.Rproj`, wiring working directories, pre-filling package-loading
boilerplate) — that kind of scaffolding is fine, but any content decisions
(what a section should contain, how to phrase something, which variable to use)
must trace back to a file in the folder.

## Keeping the folder current

When new files show up in `~/Downloads` that match course material patterns
(course-related script/data/workshop names, or anything the user identifies as
"from class"), organize them into the matching subfolder rather than leaving them
loose at the top level of Downloads. Check for exact duplicates of already-organized
files (`diff -q`) before adding — don't create redundant copies.
