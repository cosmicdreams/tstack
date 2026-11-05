# tstack

Local adaptation of [Theo's tstack](https://github.com/t3dotgg/tstack).
These delivery skills work in Claude Code and Codex. Some use [T3 Code](https://github.com/pingdotgg/t3code)
features when they are available and fall back to native tools when they are
not.

## Skills

| Skill | Say | What it does |
|---|---|---|
| `full-send` | "full send" | Takes a change to a merged PR with nobody watching: proves it, reviews it, files it, babysits it, merges it. |
| `full-stop` | "full stop" | Same as `full-send`, but stops when the PR is ready for you to merge. |
| `council` | "council" | Gets independent reviews from configured members, with bounded rounds. |
| `review-loop` | "review loop" | Reviews a change with a configured reviewer, with bounded correction rounds. |
| `file-pr` | "file a PR" | Files a short PR that leads with the problem, not an inventory of changes. |
| `takeover` | "take over" | Finishes someone else's PR, branch, or agent thread, and keeps their credit. |
| `babysit-pr` | "babysit" | Watches a PR through CI and review bots, and fixes the real findings. |
| `modernize` | "modernize" | Rebases an old PR and decides if it should still exist. |
| `leaving-pr-comments` | (automatic) | Formats comments that an agent posts on your behalf. |

Some skills call others. Install the ones they need too:

- `full-send` uses `review-loop`, `file-pr`, and `babysit-pr`.
- `full-stop` uses `full-send`.
- `takeover` uses `modernize`, `file-pr`, `babysit-pr`, and `leaving-pr-comments`.
- `file-pr`, `babysit-pr`, and `modernize` use `leaving-pr-comments`.

## Local use

Develop changes in a dedicated worktree outside CLAUDE-PLUGINS. Keep this fork
local unless publication is explicitly requested. Install all nine skills
together so their relative references resolve. Existing overlapping delivery
skills should be retired locally after validation; retain workshop's daily
planning/recap functions, process-lab's project obligations, and specialist
plugins. Council and delivery replace those uses of Octopus, not every Octopus
feature; check usage before removing it.

full-stop retains upstream's no-merge contract. The inherited workflow now
uses review-loop, golden-rule worktrees, global model routing, and project
checks and communication conventions. full-send remains explicit opt-in.

After reviewing changes and running `python3 -m unittest discover -s tests -v`,
install locally with `python3 scripts/install-local.py`. The optional
`--project-root <path>` updates the old Team Sprint Mode instruction block in
an existing non-git project container. The installer refuses repository targets.
It copies the nine skills into Claude and Codex user directories, backs up
affected files under `~/.local/state/tstack/`, and writes a manifest there.
Claude's work profile shares the personal profile's skills directory locally.

The migration disables legacy sprint/retro/improve plugins and Octopus, detaches
the exported Octopus skill symlink, and preserves source checkouts, plugin data,
boards, and history. Existing lib delivery skills become forwarding entries;
the remaining lib utilities stay installed. A lib plugin refresh may restore
its old implementations: rerun the installer after such a refresh until the
shared plugin source is deliberately migrated. Jev is disabled in Claude's
environment settings and Codex's shell environment. Restart sessions to load
the new skills and configuration. See [validation](VALIDATION.md) for limits.

## Requirements

- An authenticated [GitHub CLI](https://cli.github.com) (`gh`).
- `python3` for `babysit-pr`'s `pr-wait` script.
- A configured reviewer route for `review-loop` and configured independent
  members for `council`. Cross-provider access is optional, subject to project
  permissions. Use the host's delegation tools and actual model catalog.
- Global routing guidance at `~/.claude/AGENTS.md` and its referenced access and
  host instructions. Project AGENTS.md / CLAUDE.md owns project-specific rules.
- No fleet, OpenCode work route, or Jev dependency.

## Make them yours

These are starting points. Edit them. Put personal settings, like which models
sit on your council, in your `CLAUDE.md` or `AGENTS.md`, so you can update the
skills without losing them.

## License

[MIT](LICENSE)
