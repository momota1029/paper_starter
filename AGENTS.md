# Paper Starter — operating map

This workspace supports research writing across disciplines. Start with the
user's actual target, reader, evidence, and requested outcome. Repository paths
below are relative to this root. Read selected instructions in full.

## Routing

- Explicit `blind-referee` / 初見査読 command: read
  [.agents/skills/blind-referee/SKILL.md](.agents/skills/blind-referee/SKILL.md).
  This standalone entry is report-only, not permission to rewrite.
- Undergraduate-accessible research lecture notes: use
  [.agents/skills/undergraduate-lecture/SKILL.md](.agents/skills/undergraduate-lecture/SKILL.md)
  as a paper-writing overlay, not a second pipeline.
- CVs, grant/application forms, or resuming their interview: use
  [.agents/skills/application-interview/SKILL.md](.agents/skills/application-interview/SKILL.md).
  Keep the interview in this chat; it is not a manuscript-production task.
- Drafting, revising, reviewing, or translating a manuscript: read
  [.agents/skills/paper-writing/SKILL.md](.agents/skills/paper-writing/SKILL.md).
- Intake, project creation, indexes, or output organization: read
  [rules/workspace.md](rules/workspace.md) and [tools/README.md](tools/README.md).
- Rules, skills, tools, or template maintenance: read
  [docs/maintenance.md](docs/maintenance.md). This does not start paper production.
- An ordinary explanation in chat is not a request to create a paper.

## Invariants

1. Raw material is not verified evidence. Keep `inbox/`, authoritative sources
   in `writing/`, and generated artifacts in `output/` distinct.
2. Apply [logical writing](rules/logical-writing.md) and
   [argument audit](rules/argument-audit.md) to manuscript prose. Fluent prose,
   a successful build, and reviewer agreement do not establish correctness.
3. Choose the field, genre, language, and reader from the project contract.
   Never silently impose mathematics conventions on another discipline.
4. Preserve claim strength, uncertainty, provenance, and author decisions.
   Never invent references, data, quotations, approvals, or review executions.
5. For substantial writing, use the design → write → independent review →
   adjudicate → repair → fresh review loop in [review rules](rules/review-loop.md).
   Correctness and reader understanding have separate closure conditions.
6. The user-selected primary model remains selected. Use the shipped
   [.codex/agents/](.codex/agents/) definitions and [routing](docs/agents.md):
   Luna for bounded extraction/checks, Sol for design, writing, and substantive
   judgment. Pass model and effort as actual runtime settings, not merely as
   prompt text. Use available delegation with fresh
   context (`fork_turns: "none"` where supported) and bounded assignments.
   Explicit single-agent requests prevail; report the independence limitation.
7. Reviewers are read-only and cannot review artifacts they designed or wrote
   as independent auditors. Keep reports separate until collection is complete.
   A blind reader receives only the frozen artifact, neutral background, and
   forward-reading procedure; no rules, design, expected answers, or history.
8. Fix accepted defects and recheck affected dependencies. Never mark missing
   checks as passing, weaken reader goals to obtain a pass, or repeat an
   unchanged evaluation until a favorable answer appears. In an authorized
   revision task, continue repair and fresh checking until scoped convergence;
   no default total round cap. Authority, external-input, isolation and explicit
   resource stops remain unfinished, not a pass. Application interviews pause
   for actual user answers rather than self-generating more rounds.
9. Work within the request. Review-only means report-only. Narrow edits do not
   require regenerating companions or running a full panel. A missing author
   decision blocks only dependent work.
10. Preserve user files. No automatic commit, push, submission, email, upload,
    or copying of private research into the public starter. Prepare requested
    local artifacts and report actual checks and unresolved limitations.

Follow the user's communication preferences. Artifact language and register
follow the intended reader and venue, independently of chat style.
