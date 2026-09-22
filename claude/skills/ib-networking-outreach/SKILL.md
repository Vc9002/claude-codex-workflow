---
name: ib-networking-outreach
description: Runs a daily investment banking networking pipeline. Each run adds one new firm to a rotation across boutique IB, private equity, venture capital, private credit, hedge funds, and asset management, researches the best banker or investor to contact, writes a personalized email in the user's voice, creates a Gmail draft, and logs it to a tracker that can be a local spreadsheet or a Google Sheet. Use when the user asks to run their daily outreach, add firms to a networking pipeline, draft a networking email to a specific bank or fund, review and send queued drafts, or set up automated finance recruiting networking.
---

# Investment Banking Networking Outreach

A repeatable outreach engine for finance recruiting. One run equals one new firm added to the pipeline and one researched, personalized, logged email draft to a banker or investor.

Built around how banking and buyside networking actually works: coffee chats and informational calls compound over months, so the point is consistent daily volume with real personalization, not a blast. Every firm gets a draft, every contact gets researched, and nothing leaves the outbox without a human saying so.

Everything personal lives in the user's own config file. This skill contains no names, no bios, no firms, and no geography. Do not hard code any of those here. If a fact about the user is needed and the config does not have it, ask, then write the answer into the config so the next run has it.

## Files this skill expects

All paths are relative to the user's working folder, referred to below as `WORKSPACE`.

| File | What it is |
|---|---|
| `WORKSPACE/outreach_config.md` | Who the user is, what they are targeting, style rules, and the running firm list |
| Tracker | One row per contact drafted. Either `WORKSPACE/outreach_tracker.xlsx` or a Google Sheet. See Tracker below |

## Tracker, read this before promising a Google Sheet

Two supported backends. The config field `Tracker Backend` decides which one is used.

**`xlsx`, the default.** A local spreadsheet written with openpyxl. Fast, exact, no dependencies, works offline, preserves formatting. This is the recommended option and the one to use unless the user specifically wants a Sheet.

**`google_sheet`.** Writing to a Google Sheet is possible but is not a first class API operation in most setups, so be honest about the mechanics rather than promising a clean append:

1. **If a Google Sheets connector with a row append or cell update capability is connected, use it.** That is the clean path. Check what is actually available before claiming it works. Do not assume a Sheets connector exists because Drive is connected. A Google Drive connector alone is not enough: Drive tools typically create, read, copy, and rename files, and update only file metadata such as title and parent folder. They generally cannot write into cells.
2. **Otherwise, use the browser.** Open the Sheet in the user's browser, click the first empty cell in column A, and type the row with tab separated values, which fills across the row. Verify by reading the row back after entry. This genuinely writes to the Sheet, but it is slower than the local path and can break if the Sheet layout changes.
3. **Never silently fall back.** If the Sheet cannot be written, say so in the run output, write the row to a local CSV named `WORKSPACE/tracker_pending.csv` so nothing is lost, and tell the user which rows need importing.

Do not rebuild the whole Sheet from a CSV export to add one row. That destroys formatting, formulas, filters, and anyone else's edits.

The tracker columns are the same either way: Firm, Firm Type, Name, Title, Affiliation, Profile URL, Email, Notes, Date Drafted, Status.

## Setup, run once, and tailor it to whoever is running it

If `outreach_config.md` does not exist, do setup instead of a normal run.

Read `reference/setup_guide.md` first. It holds the full question set and the tradeoffs to explain when the person has to make a choice.

Do not open with a blank interview. Build a draft config from what can already be observed about this specific person, show it to them, and ask only about what is genuinely missing. A first run that already knows their school, their last internship, and how they actually write is the difference between a tool they keep using and one they abandon on day one.

**Step 1, gather signals before asking anything.** In parallel, and without narrating each one:

- **Resume.** Look in the working folder for a resume in PDF, docx, or markdown. Read it. It gives name, school, year, concentration, every prior role, dates, and usually the clubs and competitions that make the best email hooks.
- **Existing memory and instructions.** Check for a `CLAUDE.md`, a memory directory, or saved preferences. These often already hold writing rules, tone preferences, and career goals.
- **Sent mail voice.** With Gmail connected, read a handful of the person's own sent messages, ideally professional ones. Extract their real signature block verbatim, their typical greeting and sign off, sentence length, contraction use, and how formal they actually are. Writing the config's style rules from their real sent mail is far more accurate than asking someone to describe their own voice, which almost nobody can do well.
- **Profile.** If a professional profile URL turns up in the resume or signature, read it for anything the resume left out.

**Step 2, draft the config.** Fill `reference/config_template.md` with everything inferred. For each field, mark the source, for example `<!-- from resume -->` or `<!-- inferred, please confirm -->`. Never invent a fact to fill a blank. An empty field the person fills in is fine. A fabricated internship in a config that then feeds every email is a real problem.

Infer sensibly:

- Firm type rotation and geography from where they have worked, where they study, and what the resume points toward. Someone with two credit internships should not get a rotation weighted to venture capital.
- Positioning lines from actual experience, written one per firm type, in their voice, claiming only what the resume supports.
- Preferred affiliations from school, prior employers, hometown, and any teams, competitions, or fellowships listed.
- Writing constraints from the observed sent mail patterns.

**Step 3, confirm in one pass.** Show the drafted config and ask only about real gaps and anything inferred with low confidence. Group every question into one message. Call out specifically the positioning lines and the signature block, since those appear in every future email and are the two places a wrong guess is most visible. Also confirm the tracker backend here.

**Step 4, finish setup.** Create the tracker: run `python3 scripts/tracker.py create WORKSPACE/outreach_tracker.xlsx` for the local option, or confirm access to the Sheet and check its header row for the Google option. Confirm Gmail is connected; without it the run can still research and log, but cannot create drafts. Offer to schedule this as a recurring weekday task.

Then stop. Do not also do a full outreach run on setup day unless the user asks.

**Re-tailoring later.** If the person says drafts do not sound like them, the config is what missed, not the skill. Read the emails they actually sent or edited, compare against what was drafted, update the style rules and positioning lines in the config, and say what changed. If their situation changes, for example they accept an offer or switch target industries, update `About Me`, the rotation, and the positioning lines rather than starting over, so the firm history and exclusion notes survive.

## Part A, add one firm to the pipeline

**A1. Pick the type.** Read the config. Look at the `Firm Types Rotation` list and the existing entries in `Firms List`. Find the type of the most recently added entry that was added by the rotation, ignoring anything marked as manually requested. Take the next type in the rotation after it. If the history is unclear, pick the type with the fewest entries.

**A2. Research one firm of that type.** It must be:

- absent from the config list, checked carefully against every existing entry
- a genuine fit for the chosen type
- at or above the minimum size set in the config
- backed by something verifiable: deal history, assets under management, portfolio companies, fund closes, league table presence, funding raised, or revenue, found on the firm's own site or in reputable press
- currently active, not dormant and not a shell

Follow the geography priority in the config. Fall back to the next geography only when the primary is genuinely exhausted for that type, and say so in the entry.

**A3. Append it.** Add the firm to the bottom of the correct section of `Firms List`, numbered from the highest existing number. Include a short parenthetical: location, what the firm does, size, evidence it is real and active, why it was chosen, which prior entries it is distinct from, and any geography fallback reasoning. Future runs depend on this note to avoid duplicates, so write it for a reader who has no memory of today.

Log one line: what was added and as what type. If nothing suitable could be verified, say so plainly and continue to Part B.

## Part B, draft today's email

**B1. Find the target.** Compare `Firms List` against the Firm column of the tracker. Today's target is the first firm in the config that has no row in the tracker. If every firm has a row, stop and tell the user the pipeline is drained.

**B2. Find the contact.**

**Source hierarchy, best first.** Use the highest tier that is available and say in the tracker which tier the facts came from:

1. **Regulatory and corporate filings.** For public companies and registered advisers, proxy statements, annual reports, and adviser brochures carry officially disclosed biographies including education. This is the strongest evidence available and is worth checking first for any firm large enough to file.
2. **The firm's own team or bio pages.** Read the individual bio page, not the roster summary.
3. **Firm press releases and reputable trade press** quoting an official biography.
4. **Professional profile pages, when they load.** See the honest note below.
5. **Directory aggregators** such as contact databases. Use these for email patterns and to corroborate, never as the sole basis for a claim about a person's education or history.

**An honest note about LinkedIn.** LinkedIn blocks automated fetching of profile pages. An unauthenticated request usually returns an empty page, and scraping it programmatically breaks their terms of service and can get the user's own account restricted. Do not build a run around it and do not claim a fact came from LinkedIn when the page never loaded.

What does work: if the user is signed in to LinkedIn in their own browser, their browser can open a specific profile and the visible page can be read the same way a person reads it. That is ordinary browsing, one profile at a time, at human pace. Use it when a profile is genuinely needed and the user has asked for it. Do not loop it across dozens of profiles.

If a profile will not load, that is normal. Fall back to the tiers above and record what could not be verified rather than guessing.

**Never state a fact about a person that was not actually read on a page.** Search result summaries invent education and job history routinely. In particular, they confuse people who share a name. If the only evidence is a search snippet, treat the fact as unverified and write it that way in the tracker.

Choose one contact:

1. First choice, someone matching a `Preferred Affiliation` in the config, for example a shared school, city, employer, or program, verified on a real page at tier one, two, three, or four.
2. If no such person exists, pick the most senior appropriate contact anyway and use a hook from their actual career instead.

**Never skip a firm for lack of a shared affiliation.** A shared school is a nice hook, not an entry requirement. Skipping otherwise good firms over it silently shrinks the pipeline. The only real reasons to move on are that the firm turns out to be defunct or a shell, or that no named contact exists at all after checking the team page, filings, and press coverage. Both are rare. Note either and move to the next firm.

**Seniority.** Prefer Managing Director, Partner, Principal, Vice President, Director, Portfolio Manager, or Head of a coverage group, sector, or strategy.

A note on who actually replies. Analysts and Associates answer most often but can do least for the user and know least about the long arc of a career. Managing Directors and Partners answer least often but a single reply is worth far more. Vice President and Principal level is usually the sweet spot: senior enough to matter, close enough to their own recruiting to remember what it felt like. Aim there when the choice is open.

Prefer to avoid founders, CEOs, and entry level titles. This is a preference, not a wall: at a small firm where the only identifiable people are a founder and an associate, draft to the better of the two and note the exception.

**Hard exclusion, support functions.** Never draft to anyone whose primary job is Human Resources, People, Talent, Recruiting, Learning and Development, Payroll, Marketing, Brand, Communications, Public Relations, Events, Legal, Compliance, Regulatory, internal Finance, CFO, Controller, Treasury, Tax, Audit, Risk, Sustainability or ESG, internal IT or Security, Investor Relations, or administration.

Unlike the founder and CEO rule, this one has no escape hatch. If the only people found are support function people, keep looking through the team page, filings, and press coverage until someone on the line side turns up.

The reason is that the user is networking to learn how deals and investments actually get done and to reach the seats where that happens. A very senior person in a support function cannot speak to live deal flow, how a pitch gets built, or how an investment committee decides, however impressive their background, and cannot pull a resume into a live process. Target instead: bankers on coverage or product teams, deal professionals, portfolio managers, sector and strategy heads, and research analysts. At operating companies, target corporate development, strategy, product, and profit and loss owning leaders.

Recruiting and HR is the sharpest version of this trap, because those people are the easiest to find and the most likely to reply. A friendly reply from a campus recruiter is not the same as a relationship with someone on the deal team, and time spent there is time not spent on the people who can actually vouch for the user later.

Judgment notes:

- A Chief Operating Officer is usually a genuine business leader and is allowed, unless the role is plainly pure administration.
- Judge the current role, not the career history. Someone who spent years as a CFO and now runs a business unit as President is a line contact today.
- A sector in a title is not a function. "Analyst, Communications and Media" is a research role covering a sector, not a communications job. Read the function, not the keywords.
- Dual roles qualify on the line side half, for example "Head of Sustainability and Head of Client Investment Strategies".
- Chief Technology Officer is excluded at investment firms where it is a support function, and allowed at technology companies where it is core product leadership.
- Someone with a preferred affiliation in a support function seat does not beat a non affiliated person on the line side. Seniority and affiliation never override this exclusion.

**B2 check.** Before continuing, confirm out loud: which source tier the background came from; that any affiliation claim is stated explicitly on that page, and if it is not, that the person is being treated as unaffiliated with a career hook instead; that the title is as senior as reasonably available; and that the exact title passes the support function exclusion. State the title and the verdict. If it fails, discard and go find someone else.

**B3. Find the email.**

1. Check the bio page or filing for a listed address.
2. Confirm the real email domain from the firm's own site. Do not assume it matches the firm name.
3. Search for the verified pattern, for example `[firm] email format site:rocketreach.co`, and cross check other directory sources.
4. Build the address from the verified domain and dominant pattern.
5. Record confidence: HIGH, MEDIUM HIGH, MEDIUM, or LOW, plus where the pattern came from.

Watch for the formal versus preferred name problem. Someone publicly known as Bill may have a corporate address built from William, or the reverse. When the bio gives both, note the alternate in the tracker so a bounce has an obvious second try.

End this step by writing the address down explicitly: "Contact email for this run: [address]." That exact string is what goes in the draft.

**B4. Decide attachments.** Read the `Attachment Rules` section of the config, which maps firm types to whatever the user attaches. Attachment reminders go in the tracker Notes column only. Never mention an attachment inside the email body.

Most connectors cannot attach real files to a draft reliably. Do not try to pass files as base64. Put a reminder in Notes so the user attaches them by hand before sending.

**B5. Write the email.**

Tone: warm, genuine, curious. A real person who wants to learn something, not someone working a list.

Subject: `[the user's own context or a shared hook] interested in [something specific about the firm or the person's path]`. Never use the word "attached". For unaffiliated contacts, lead with the user's own context rather than implying a shared tie that does not exist.

Body, three to four short paragraphs, no bullets:

1. Greeting, who the user is in one line from the config, and the specific reason they came across this person.
2. One concrete observation about that person's actual path. A career pivot, a sector niche, unusual tenure, a shared background, or something odd about how they got there. No generic praise. Nothing invented. For unaffiliated contacts this paragraph carries the whole email, so make it genuinely specific.
3. One line about the user, chosen from the `Positioning By Type` section of the config to match this firm type. Then one sentence naming what they would like to hear about, specific to this person.
4. A light ask for a short conversation in the next couple of weeks, flexible to the contact's schedule.

Then the signature block from the config.

Apply the `Writing Constraints` from the config, for example banned characters, banned phrases, and length limits.

**B6. Check the email.** Verify every item before creating anything:

- writing constraints respected throughout subject and body
- subject does not contain "attached"
- paragraph two rests on something actually read on a real page, at a named source tier
- if the contact is unaffiliated, nothing in the email implies a shared school, employer, or program
- no mention of attachments, resumes, or other materials anywhere in the body
- no stray blank line between the greeting and the first paragraph
- **recipient gate:** restate the address from B3 and confirm it belongs to the researched contact, with their name in the local part, and is not the user's own address. Addressing a draft to the user instead of the contact is a real failure mode and this check exists to catch it
- **support function gate:** restate the title one last time and confirm it is line side

Fix anything that fails before moving on.

**B7. Create the draft.** Use the Gmail draft tool with the researched address in `to`, passed as a list. Never the user's own address. If B3 could not verify anything, still use the best guess for the contact, never blank and never the user, and mark it LOW.

Use the HTML body field with `<br>` tags only. `<p>` tags introduce spacing gaps. Structure:

```
Hi [Name],<br><br>[paragraph 1]<br><br>[paragraph 2]<br><br>[paragraph 3]<br><br>[paragraph 4]<br><br>[sign off],<br><br><br>[signature block from config]
```

**Signature rendering, tested behavior.** Gmail rewrites HTML on save. Verified by round tripping a draft through the API and reading it back:

- `&nbsp;` is converted to an ordinary space. Do not rely on it to hold separators together. Keep signature lines short enough that they do not wrap, or put each item on its own line, rather than depending on non breaking spaces.
- Gmail wraps every http and https link in a `google.com/url?q=` redirect, even when the anchor is already a clean absolute URL. This is Gmail's own behavior on all outbound mail, it is not a defect in the signature, and it cannot be prevented through the API. Do not spend time trying to fix it.
- `mailto:` links are left alone and stay clean.
- Inline styles survive. Dividers built from a styled `<span>`, an `<hr>`, or a single cell `<table>` all round trip intact in Gmail. The table version is the most conservative choice if the recipient may be reading in Outlook, which handles `display:block` on a span less predictably.

Write the signature as one line of HTML with no line breaks inside it, since stray newlines in the source can become unwanted spacing.

**B8. Log it.** Append a row to the tracker with: Firm, Firm Type, Name, Title, Affiliation (exactly as written on the page, or "Not verified"), Profile URL, Email, Notes, Date Drafted, Status.

Set Status to `drafted`.

Notes always starts with "Gmail draft created." then adds the attachment reminders for this firm type, the email confidence level and its source, the source tier the biography came from, whether the contact is unaffiliated and that the hook is career based, and which other senior people were checked and excluded and why, including anyone dropped under the support function rule. That exclusion log is what stops a future run from redoing the same research.

For the local tracker, use the script rather than hand written spreadsheet code, so formatting stays consistent and the duplicate guard runs:

```
python3 scripts/tracker.py append WORKSPACE/outreach_tracker.xlsx \
  --firm "..." --type "..." --name "..." --title "..." \
  --affiliation "..." --url "..." --email "..." --notes "..."
```

It refuses to add a firm that already has a row, which is the main protection against a rerun logging the same contact twice. If that guard fires, stop and work out why the firm was selected again rather than passing `--allow-duplicate` reflexively.

If the Google Sheet path fails, stage the row instead so nothing is lost:

```
python3 scripts/tracker.py pending WORKSPACE/tracker_pending.csv --firm "..." [same flags]
```

Finish by confirming the Email cell matches the draft `to` field character for character.

## Sending, only with a human in the loop

The skill drafts by default. It does not send on its own, on a schedule, or as part of a normal run.

When the user asks to send, run this flow:

1. **Show the queue.** List every tracker row with Status `drafted`, with contact name, firm, title, the subject line, and the email confidence level. Show the full body of any draft the user asks to see.
2. **Get explicit approval.** The user names which ones to send, or says all. Silence, a thumbs up on an unrelated message, or a general instruction given days earlier is not approval.
3. **Send only those.** After each send, set that row's Status to `sent` with the date.
4. **Report** what was sent and what was skipped.

Never send a draft the user has not seen. Never send in the same turn the draft was created unless the user reviewed the body in that turn and said to send it.

**Why the gate is here, since it will be tempting to remove it.** A send is irreversible. The three failure modes this catches are all real and all happen:

- A confidently wrong fact about the recipient's background, drawn from a search snippet about a different person with the same name. Recoverable in a draft, permanently embarrassing once sent.
- A guessed email address. Anything below HIGH confidence is roughly a coin flip, and bulk sending to unverified addresses drives bounce rates that damage the sending domain's reputation and can get the account throttled or flagged as spam.
- The wrong recipient entirely, which is exactly what the B6 recipient gate exists to catch and exactly the kind of error that slips through when nobody reads the output.

Cold outreach at volume without review is also how a name gets burned at a firm permanently. One careless message to an MD costs more than the twenty good ones gained by skipping review.

If the user wants to loosen this, the honest options are to approve a batch at a time after reading it, or to auto send only to addresses marked HIGH confidence while holding the rest. Fully unattended sending is not recommended and should not be enabled quietly.

## Follow ups

If the config enables follow ups, flag tracker rows with Status `sent` older than the configured window with no reply logged. Draft a single short follow up for the user to review. One follow up maximum. A second is noise.

## Run output

Report: the firm added and its type, today's target and contact with title, the source tier the biography came from, affiliation status, who was excluded and why, the email address and its confidence, which tracker backend was written and whether the write succeeded, and confirmation that a draft was created and verified. Flag any judgment call worth a second look.
