# Outreach Config

Copy this to `WORKSPACE/outreach_config.md`. The skill reads this file on every run and writes new firms to the bottom of it. Nothing personal lives in the skill itself, so this file is the single source of truth.

On first run the skill fills most of this in automatically from the person's resume, saved preferences, and their own sent mail, then asks only about the gaps. The `[ ]` placeholders are what remains when there is nothing to infer from.

Mark the origin of each filled field so it is obvious later what was read and what was guessed:

- `<!-- from resume -->` for facts read directly
- `<!-- from sent mail -->` for voice and signature details
- `<!-- inferred, please confirm -->` for anything reasoned rather than read

Never fabricate a fact to fill a blank. An empty field is fine. An invented internship feeds every future email.

Defaults below are set for an undergraduate or early career candidate recruiting into investment banking and the buyside. Change anything that does not fit.

---

## About Me

- Name: [ ]
- School or current employer: [ ]
- Year or level: [ ]
- Concentration or focus: [ ]
- Current or upcoming role, if any: [ ]
- Prior experience worth mentioning, two or three items maximum: [ ]
- Distinctive personal details that make good hooks: [ hometown, sport, competition, language, military service, first generation, career switch, anything real and specific ]
- What I am actually trying to learn or reach: [ ]

One line self introduction used in paragraph one of every email:

> I'm [name], a [year] at [school] studying [focus], and I came across your background while [specific reason].

## Contact Details For The Signature

- Email: [ ]
- Phone: [ ]
- Profile URL: [ ]

## Tracker Backend

Which tracker the skill writes to. One of `xlsx` or `google_sheet`.

- Backend: [ xlsx ]
- Local tracker path: [ WORKSPACE/outreach_tracker.xlsx ]
- Google Sheet URL, only if backend is google_sheet: [ ]

`xlsx` is the default and the reliable one. Choose `google_sheet` only after reading the Tracker section of SKILL.md, which explains what writing to a Sheet actually requires. A Google Drive connector on its own cannot write cells, so without a Sheets connector that supports row append or cell update, the Sheet gets written through the browser, which works but is slower and more fragile.

## Signature Block

One line of HTML, used verbatim at the bottom of every draft. No line breaks inside it. Replace the bracketed parts.

```html
<strong style="font-size:16px;">[Full Name]</strong><table cellpadding="0" cellspacing="0" border="0" style="width:260px;border-collapse:collapse;"><tr><td style="border-top:1px solid #cccccc;font-size:0;line-height:0;height:6px;">&nbsp;</td></tr></table>[Degree] Candidate | [School]<br>[Phone] | <a href="mailto:[email]">[email]</a> | [profile URL]
```

Three things about this, all confirmed by round tripping a real draft through Gmail rather than assumed:

- `&nbsp;` becomes an ordinary space when Gmail saves the draft, so it cannot be used to protect the spacing around the pipe separators. Keep each line short enough that it does not wrap, or split the contact details across two lines.
- Gmail rewrites every http and https link into a `google.com/url?q=` redirect, even a clean absolute one. Every Gmail user's links look like this. It is not a defect and cannot be prevented through the API.
- `mailto:` links are left untouched, so the email address stays clean.

The table based divider is used because it renders most consistently across mail clients. A styled `<span>` or an `<hr>` also survives Gmail, but Outlook handles them less predictably.

## Preferred Affiliation

Shared ties the skill looks for first when picking a contact. Preferred, never required. A firm never gets skipped for lacking one.

- School or alumni network: [ ]
- Former employers: [ ]
- Hometown, region, or country: [ ]
- Programs, clubs, teams, fellowships, or competitions: [ ]

## Geography Priority

Work through these in order. Only fall back when a tier is genuinely exhausted for a given firm type, and say so in the entry.

1. [ primary city or metro ]
2. [ secondary, usually New York for finance ]
3. [ anywhere else that clears the quality bar ]

## Minimum Quality Bar

- Minimum employees: [ 10 ]
- Must have verifiable evidence of activity: deal history, assets under management, portfolio companies, fund closes, league table presence, or press coverage
- Exclude: dormant firms, shells, single person shops below the employee floor, and anything already on the list

## Company Types Rotation

Add one firm per run, cycling through this list in order. Adjust to match what the user actually wants.

1. Boutique Investment Bank or M&A Advisory
2. Private Equity
3. Venture Capital
4. Private Credit
5. Hedge Fund
6. Asset Management
7. Growth Equity
8. Restructuring or Special Situations
9. Middle Market or Regional Bank
10. Corporate Development or Strategic Finance at an operating company

Optional extras if the user wants exposure beyond finance: startups, big tech product, media, telecom, AI and frontier tech, fintech infrastructure.

## Positioning By Type

The single line about the user in paragraph three, matched to the firm type. Rewrite these in the user's own voice. Keep each to one sentence and keep them honest.

- Boutique IB: [ e.g. I'm recruiting into banking and have been drawn to how differently middle market advisory work looks from bulge bracket coverage. ]
- Private Equity: [ ]
- Venture Capital: [ ]
- Private Credit: [ ]
- Hedge Fund or public equity: [ ]
- Asset Management: [ ]
- Growth Equity: [ ]
- Restructuring: [ ]
- Corporate Development: [ ]

Rule for all of them: claim only what is true. An interest is not experience. If the user has never built a model, do not say they have. Bankers spot inflated claims instantly and it is the fastest way to lose a contact permanently.

## Attachment Rules

What to attach, by firm type. These are reminders written to the tracker only. The email body never mentions an attachment.

- All firm types: [ resume ]
- Hedge Fund, public equity, VC: [ resume and a stock pitch or investment memo, if the user has one worth sending ]
- Everything else: [ resume only, pure networking ]

Files live at:

- Resume: [ path ]
- Pitch or memo, if any: [ path ]

## Writing Constraints

- Banned characters: [ e.g. hyphens and em dashes, or leave blank ]
- Banned phrases: [ e.g. "by way of context", "I wanted to reach out to", "no agenda beyond", "I hope this finds you well" ]
- Length: three to four short paragraphs, no bullet points, no more than roughly 150 words
- Voice: warm, specific, curious, and plainly a student or early career person. Not corporate. Not a cover letter.
- Never claim a shared affiliation that was not verified on a real page
- Never use the word "attached" in a subject line

## Sending Rules

- Runs create Gmail drafts. Runs never send.
- Sending happens only when the user asks, after they have seen the queue, and only for the messages they name. See the Sending section of SKILL.md.
- One contact per firm per run.
- Do not contact anyone already in the tracker without an explicit instruction.

Send mode: [ review_then_send ]

Options and what they mean:

- `draft_only`: the skill never sends under any circumstances. Safest.
- `review_then_send`: the default. The skill shows the queue, the user names which to send, the skill sends those and marks them sent.
- `auto_send_high_confidence`: sends without review, but only to addresses marked HIGH confidence, holding everything else for review. Not recommended. A HIGH confidence pattern match is still a guess about one specific person, and this mode will eventually send a message built on a fact nobody checked.

Fully unattended sending of every draft is deliberately not an option. A bad cold email cannot be recalled, and bulk sending to guessed addresses damages the sending domain's reputation.

## Follow Up Policy

Optional, off by default. If enabled, the skill flags contacts in the tracker who were drafted more than [ 10 ] business days ago with no reply logged, so the user can decide whether to follow up once. One follow up maximum. A second is noise.

## Firms List

Firms are appended here by the rotation, numbered, newest at the bottom. Each entry records location, what the firm does, size, evidence it is real and active, why it was chosen, and which existing entries it is distinct from.

Start it with any firms the user already cares about, or leave empty and let the rotation fill it.

### Boutique Investment Bank or M&A Advisory

1. [ first firm ]
