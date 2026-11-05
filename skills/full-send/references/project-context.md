# Project context for delivery and review

Read the applicable global and project AGENTS.md / CLAUDE.md instructions before
acting. Follow their referenced files when relevant. Reuse existing project
process configuration (including process-lab when configured); do not invent a
second gate table. This reference supplements the task, not its authorization.

## Worktree and resources

Before any edit, check the destination worktree and branch. Changes, including
documentation and review fixes, belong in a dedicated worktree on its own
branch. A feature branch inside the main reference checkout is insufficient.
Create a sibling worktree automatically when needed. Never move or discard
someone else's changes, disable the write guard, or edit main to prepare work.
Use the harness's worktree isolation for delegated writers when required by
its orchestration rules; do not prepare a child's checkout in its prompt.

Work on this laptop. Default to one implementation task and one reviewer at a
time. Serialize heavy builds, browser checks, and development environments.
Council members may run sequentially with independent context. Do not assume
remote hosts, a fleet, or an always-awake machine. After interruption, inspect
live PR state, current diff, checks, and existing watcher ownership before
resuming. Old approval does not cover new behavior changes.

## Review routing

Use the user's global model-routing guidance, including its account denylist,
allowance check, review tier, and host-specific orchestration rules. In this
local setup the guidance is ~/.claude/AGENTS.md and its referenced
model-access.md and t3.md; load it even in a host that does not import it.
Keep model choices and rankings there rather than embedding copies in skills.

Filter candidate routes by the project's provider/data permissions before
ranking them. Approved external reviews are supported; this skill does not
itself authorize sending company context to another provider. When that
boundary is missing and matters to the selected route, ask for it before
sending context. Never use OpenCode for work, including helpers and fallbacks.
Do not add Jev/TypeSafe calls to this workflow. Record the actual reviewer and
route used. If a named route is unavailable, report it instead of silently
substituting.

## Naming models

Wherever you name a model, use its exact model ID as the host reports it,
such as `gpt-6.1-sol` or `claude-opus-5-5`. This covers delegation requests,
briefs, ledgers, reports, questions to the user, PR descriptions, and
comments. Never write a family name (`Sonnet`, `GPT`), an alias (`sonnet`,
`opus`), a provider alone, or a version-less name; they hide which model ran.

- Effort: write `<model-id> (<effort>)`, and only when the host confirms the
  effort that ran. Never assume a default.
- Route: name it separately, such as `gpt-6.1-sol via T3 delegate_task`. A
  route, harness, or CLI is not a model. Antigravity is a route.
- Requests: ask for the exact model ID, then record the ID the host reports
  back. If it differs from the request, say so.
- Unknown: write `model not reported` and name the harness. Never infer the
  model from an alias, a catalog default, or another CLI.

## Readiness and communication

Resolve the intended base branch, covering local checks, required CI checks,
required reviewers/bots, and any required human approvals from project guidance
and live repository rules. Inspect CI configuration when commands are unclear.
An unknown or unreadable requirement is not a passing gate. Do not invent a
review-bot requirement for a repository that has none, waive a required human
approval, or treat a review-loop verdict as proof of complete PR readiness.

Project guidance owns title conventions, voice, attribution, and bot reply
syntax. The communication skills provide defaults only where the project has
no rule. Keep an accurate local record of model usage; never make a false
attribution claim. A writing convention does not grant provider access.

full-stop means an open, unmerged PR, with auto-merge and queue entry prevented
as its skill specifies. full-send adds merge authority only when explicitly
requested. Generic requests to review or implement do not grant either mode.
