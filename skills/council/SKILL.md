---
name: council
description: Trigger this if the user says 'council'.
---

# Council

Before an audit, address outstanding PR comments, fix known issues, and run
relevant checks. Give council the updated implementation; do not defer known
fixes until reviews return. If the user wants to discard the implementation
and explore new ideas, skip fixes to code being replaced.

Bring independent delegates to the user's request, usually for review or
feedback. Read [project context](../full-send/references/project-context.md)
first. Resolve members from the user's global routing guidance and project
permissions. Prefer distinct providers where permitted and available, but
multiple agents from one provider can supply independent perspectives.
Honor explicitly named members; report an unavailable member rather than
silently replacing it. If membership is unspecified, use three reviewers
with correctness, scope/simplicity, and verification perspectives. Resolve
each model through the routing guidance; do not require three providers.
Name every member by exact model ID, following "Naming models" in project
context. Members on the same model ID are told apart by perspective, such as
`claude-opus-5-5 (high), correctness`.

On this laptop, run members sequentially by default. Keep their initial
contexts independent: give each the same request and artifacts, not earlier
members' verdicts. Do not start a worker fleet. Use more concurrency only when
the user requests it or global guidance provides an explicit resource limit.

Follow the host's orchestration rules. In T3, call
`orchestrator_capabilities` once and use `delegate_task` when another
provider, requested settings, background execution, or worktree isolation
requires it. Put verified effort settings in `target.options`. Start a fresh
review delegate for every new pass. Follow its completion notice; do not
poll. Cancel replaced or unneeded delegates. Elsewhere use a configured route
that actually runs each selected member. Do not silently change routes on
failure. A failed or missing response is not approval.

Give each delegate the relevant context, scope, checks, and requested return
format. Review delegates must remain read-only and must not start subagents,
edit files, post comments, or watch PRs. Do not edit the scoped files while
reviewers are running.

Ask reviewers to distinguish blockers, real in-scope bugs, and optional nits;
request evidence and a verdict. For code, each blocker or bug must carry a
proof you can rerun: the command and the output it printed, or the file and
line that shows the defect, plus the behavior the intent requires. Rerun or
reread each proof before fixing. A finding whose proof does not reproduce is
recorded as `dropped: not reproduced`, and the report counts dropped findings
per member. (Adapted from pstack's interrogate, Lauren Tan, MIT.) Scores out of 10 may accompany code reviews,
but a score is not an approval or readiness gate. Record absent scores as
`no score`, never invent them.

Default to at most three rounds. Round one covers the full change; later
rounds cover changed code and open findings. Verify each finding yourself,
make the smallest justified fixes, and rerun covering checks. Record accepted,
disputed, declined, and dropped findings with evidence. Stop early when the current
behavior diff is approved and no blocker remains. Nits do not require another
round. Do not let repeated reviews expand scope or chase unanimity forever.

If a blocker remains disputed after two replies, a member cannot finish, or
the round budget ends, report the unresolved issue and both sides. Do not
claim consensus or let full-send merge on an incomplete review.

Report members actually used by exact model ID, perspectives, rounds, verdicts, useful findings, dropped counts,
disagreements, checks, and next steps. For an authorized PR update, include
the results in its description using the project's communication conventions;
do not post a separate comment just for the council. Otherwise report locally.
Council feedback alone does not authorize a PR update, push, or merge.
