# graphify
- **graphify** (`~/.claude/skills/graphify/SKILL.md`) - any input to knowledge graph. Trigger: `/graphify`
When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

# task-observer
At the start of any task-oriented session — any interaction where you will use tools and produce deliverables — invoke the task-observer skill before beginning work. When loading any skill, check the observation log for OPEN observations tagged to that skill and apply their insights to the current work.

# crim-coursework
- **crim-coursework** (`~/.claude/skills/crim-coursework/SKILL.md`) - any CRIM 1200 / criminal justice coursework help.
Whenever the user asks for help with CRIM coursework (exercises, datasets, codebooks, workshops, or files under `~/Downloads/Criminal_Justice_Data`), invoke the crim-coursework skill before answering, and follow its rule that all course-content answers come only from files in that folder — never outside sources or general knowledge.
