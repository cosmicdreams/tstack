---
name: review-loop
description: Use when the user says "review loop".
---

# review-loop

Review a change with one independent reviewer from a different model family
than the implementer, address real findings, and
recheck the current diff within a bounded budget. This establishes reviewer
approval, not complete PR readiness or permission to push or merge.

Read [project context](../full-send/references/project-context.md) first.
Make the smallest justified fixes. Push back on findings with evidence.

## Budget

- Default: 3 rounds total. Round 1 is full. Later rounds check only
  changed code and open findings.
- Extend to 5 only for security, permissions, auth, data loss, or
  state/concurrency, while a blocker or should stays open with evidence. Or when
  the user asks.
- Stop early if a round returns only nits. Declined nits and comment,
  doc, or format-only fixes need no new round.
- One reviewer only. The reviewer must not start subagents or reviewers.
- Keep a ledger: implementer and reviewer model IDs, then per finding id,
  severity, outcome, usage if returned. Never guess it.
- Save the ledger after each round, outside the repository, as JSON Lines at
  `~/.local/state/tstack/review-ledgers/<owner>-<repo>/<branch>.jsonl`
  (`/` in the branch becomes `-`). Append one line per finding per round:
  `{"date","repo","branch","pr","round","implementer","reviewer","id","severity","file","claim","outcome"}`,
  with `pr` null for local work and `outcome` one of `open`, `fixed`,
  `disagree`, `declined`, `dropped`. A round with no findings appends one line
  with `id` null. workshop:harden reads these files to find repeated mistakes.

## 1. Scope

Run `git status --short`. Do not stash, discard, or include unrelated
changes. Limit review to the change paths if they separate cleanly.
Otherwise stop and ask.

Find the base after `git fetch origin`:

- PR: `gh pr view <n> --json baseRefName,headRefOid`. Resolve a dedicated
  worktree for the PR; never check it out inside the main reference checkout.
  Confirm `HEAD` is the PR head, or ahead only by this change. Base: `git merge-base HEAD origin/<baseRefName>`.
- Local: resolve the intended target from the task and project guidance, using
  the default branch only when no other target is established. Use
  `git merge-base HEAD origin/<target-branch>`. No remote: a base the user names,
  or `HEAD` for uncommitted changes only.

The change is base to working tree in those paths, with untracked files.
Use one diff command all rounds. State intent and out-of-scope in 1-2
sentences. Run covering checks, starting with the project's changed-files
check command when its instructions name one. Do not send code this change
breaks. Note missing or pre-failing checks in the brief.

Find the project's agent rules: the repository's root `AGENTS.md` or
`CLAUDE.md`, plus the testing or review documents they link. List those paths
in the brief as `Rules:`, or write `Rules: none`.

## 2. Start the reviewer

The reviewer must come from a different model family than every model that
wrote the change: you, and any subagent or prior agent whose code is in the
diff. If `gpt-6.1-sol` implemented, no GPT model reviews; if
`claude-opus-5-5` implemented, no Claude model reviews. Record the
implementer model IDs in the ledger first. If you cannot identify them, report
that instead of picking a reviewer.

Resolve the reviewer from the global routing guidance's other-family review
rule and applicable project permissions described in project context. Record
provider, exact model ID, and effort only when exposed, following "Naming
models" in project context. If no eligible other-family route is available,
report the blocker. Never fall back to the implementer's family, even at a
different tier, effort, or model ID.

Follow the host's orchestration rules. In T3, call
`orchestrator_capabilities` once before delegation and use `delegate_task`
for another provider, requested settings, worktree isolation, or background
work. Put effort in `target.options`. Use a fresh delegate for each review
round (`role: "review"`, `mode: "async"`) and save its taskId. Native
subagents are suitable when the host permits the chosen provider and settings.
Outside T3, use a configured route that actually runs the selected model.
Do not silently switch providers, models, accounts, or orchestration methods
when the selected route fails.

Do not edit scoped files while review runs. Wait for the notice. Do not
poll or start a second reviewer. Timeout, error, or no reply is not
approval. On failure, cancel the task and follow the host's completion
notice before restarting with the ledger. Cancel any reviewer replaced or no longer needed.

Round 1 brief (T3 children get no history):

```
Review only. Do not edit, commit, push, comment on PRs, or start subagents.
Repo: <abs path> Base: <sha> Intent: <intent> Out of scope: <scope> Checks: <results>
Rules: <paths or none>
See: git diff <base> [-- <paths>]; git status --short (read untracked).
Read surrounding code. Find bugs, broken callers, mismatch with intent.
Read Rules. Flag a surface or entry point its checklist names that the
intent needs and the change skipped, a test its testing policy forbids or
requires, and a pattern one of its listed checks would reject.
Skip style unless it hides a bug. Hold to the smallest change. Flag code,
tests, or guards the intent does not need. Other paths, rare cases, small
perf, extra compat: nits.
blocker = intended case wrong. should = real bug callers will hit, in intent. nit = rest.
Reply:
VERDICT: APPROVE or CHANGES
S1 [blocker|should|nit] <file>:<line> <claim>. Fix: <suggestion> (stable ids)
Proof (blocker and should only): <command> -> <output it printed>, or the
<file>:<line> text that shows the defect, plus what the intent requires.
A blocker or should without a proof you checked is a nit.
```

## 3. Answer findings

Check each finding and severity yourself. Another path, rare case, or
small cost is a nit, whatever label it came with. Rerun or reread each
blocker and should proof before fixing. A proof that does not reproduce goes
in the ledger as `dropped: not reproduced`; report the dropped count.

- Agree: smallest fix. Prefer delete or narrow over new lock, cache,
  helper, or option. Fix the case that happened. Add one focused test
  that fails without the fix, if intent needs it.
- Disagree: say why, with evidence (file:line, test, output).
- Out of scope or nit: decline in one line. List as follow-up.

Update the ledger. Re-run checks and `git diff --shortstat <base>`. If
review grew the diff, cut first. Do not agree just to end the loop.

## 4. Next round

Start one only if budget remains and a blocker or should is open, behavior code
changed, or approval does not cover the current behavior diff. Use a fresh
`delegate_task` in T3, or follow up the saved native ID. Send the round 1 brief,
the ledger (`fixed:` / `disagree:` / `declined:` / `dropped: not reproduced:` + evidence), the same base
diff, and the change since last round. Tell the reviewer to check open ids and
changed code only.
Mark each old id `resolved` or `still open: <reason>`.

## 5. Stop and ship

Agreed: APPROVE on the current behavior diff, no blocker or should open,
no concern of your own. Stuck: an item stays disputed after two replies,
or budget ends. Show both sides in 2-3 lines each. The user decides.
Budget end is not approval.

Do not push during the loop. Push after agreement only if the user asked
to push, ship, or update the PR. If you push to a PR, include the review result using the project's
communication conventions. Where permitted, use:

`Reviewed with review-loop: <N> rounds with <model-id>. Verdict: approved`.

For example: `Reviewed with review-loop: 2 rounds with gpt-6.1-sol (high).
Verdict: approved`. Only claim approval on the current behavior diff. Add
effort only if verified. Keep the exact model ID and review ledger in the
local handoff even when the project uses a different public description format.

Report: rounds, exact model ID, what the review changed, diff size before/after, fixed,
declined, and dropped (not reproduced) findings with reasons, usage if exposed (else say not), pushed or not.
