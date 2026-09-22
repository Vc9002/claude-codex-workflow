# Setup Guide

Run this once, before the first outreach run. Two or three minutes if a resume is available, ten if starting cold.

## What the user needs first

- A folder for this work. Everything lives there: the config, the tracker, the resume.
- Gmail connected. Without it, research and logging still work, but drafts cannot be created.
- A resume saved in that folder as a PDF. This is the single highest value input, since it fills most of the config on its own.

## Auto tailor first, ask second

Follow the setup steps in SKILL.md: read the resume, any saved memory or instructions, and a sample of the person's own sent mail, then draft the config from those and confirm it in one pass.

The questions below are the fallback. Ask only the ones the gathered material did not already answer, and ask them together in one message rather than one at a time.

Anything inferred rather than read directly should be shown as an inference the person can correct. Do not present a guess as a fact about their own life.

## Questions, only for the gaps

**Identity and story**

1. Name, school or employer, year or level, and focus.
2. Any role already lined up, and any prior internships or jobs worth naming.
3. Two or three specific things about them that are not on a resume: hometown, a sport, a competition, a language, a career switch, a company they built. These become email hooks and are the difference between a message that gets a reply and one that gets deleted.
4. What they are actually trying to get out of this. A summer analyst seat, a full time role, a lateral move, or genuine exploration.

**Targets**

5. Which firm types they want in the rotation, and whether they want anything outside finance.
6. Geography, in priority order.
7. Any firms already on their list.
8. Any firms to avoid, for example a current employer, somewhere they already applied, or somewhere a family member works.

**Ties**

9. School and alumni network, former employers, hometown, and any programs, clubs, teams, or competitions. These are what the skill looks for first in a contact.

**Style**

10. Anything they never want in their writing. Characters, phrases, or tone.
11. Whether they want a pitch or memo attached for hedge fund and VC contacts, or resume only everywhere.

**Mechanics**

12. Where the tracker should live: a local spreadsheet, or a Google Sheet they already have. Explain the tradeoff honestly rather than just taking the answer. Local is exact and instant. A Google Sheet is shareable and viewable from a phone, but writing to one needs either a Sheets connector that supports row append, or the browser, which is slower and can break if the sheet layout changes.
13. Whether they want the ability to send from here at all, or drafts only. Default is review then send: they read the queue, name the ones to send, and those go out.

## Then

1. Write the answers into `WORKSPACE/outreach_config.md` using `config_template.md` as the shape.
2. Run `python3 scripts/tracker.py create WORKSPACE/outreach_tracker.xlsx` to build the empty tracker, or confirm access to their Google Sheet if they chose that backend.
3. Show the user the config and ask them to correct anything that sounds off, especially the positioning lines. Those lines go in every email and are the part most likely to sound like someone else wrote them.
4. Offer to schedule the skill to run automatically, for example every weekday morning.

Do not do a full outreach run on setup day unless asked.

## A word about volume

One firm per run is deliberate. A pipeline built at one genuinely researched contact per weekday is roughly twenty a month and over two hundred a year, all of them personalized, all logged, none duplicated. That beats a hundred templated emails in a weekend by a wide margin, and it is the version that does not burn a name permanently.

The failure mode is not too few emails. It is sending a message that is obviously mail merged to someone whose colleague received a near identical one.

## Honest limits worth telling the user

- Guessed email addresses bounce. Anything below HIGH confidence is a coin flip, and a bounce costs nothing but is not a delivered email either. The tracker records confidence for exactly this reason.
- Reply rates for cold outreach are low even when everything is done well. Ten to twenty percent is a normal range. That is not a reflection of the user.
- This skill drafts. It does not send, and it cannot tell whether a message is worth sending. The user reads every draft before it goes out, and should delete the ones that feel forced.
