# Local workflow validation

Source baseline: upstream/fork commit 7de017b3fc9d50c03cf3ecb98fb71e0ca65a78bd,
plus upstream fixes through 1085050f3baed1ac724caa4a8166145fb2ac88af.
All development is on feature/local-workflows in a dedicated sibling worktree.
No publication or source commit is required for this local installation.

The full-stop skill is byte-identical to upstream. Its inherited dependencies
now resolve the intended base, require final-diff review, and obey project
checks, communication conventions, golden-rule worktrees, and global routing.

Validation performed:

- Frontmatter validation for all nine skills; every relative Markdown link
  resolves. The bundled pr-wait helper starts and displays its CLI help.
- Seven installation tests cover complete dependency copies, backups, retained
  utilities, configuration preservation, repeat runs, trailing TOML comments,
  Jev opt-out, safe symlinks, repository-target refusal, and structural/config
  preflight failures. git diff --check passes.
- Independent read-only review found wrong-base and final-diff review gaps;
  both were corrected. An older unresolved finding now survives a new push.
- A second independent review reproduced installer edge cases in temporary
  fixtures. Symlink guarding, commented TOML, and preflight ordering were fixed
  and regression-tested. Local review now uses the intended target too.

Independent instruction-level dry-run:

| Case | Outcome |
| --- | --- |
| release/2.x, green checks, auto-merge/queue active, required human missing | Prevent automatic merging first; verify all other gates, then report waiting for required approval. Leave open and unmerged. |
| develop, required Arnica, older unresolved finding, meaningful conflict fix | Carry forward the finding, use the project's bot rules, renew proof/review on the final diff, and wait for Arnica. Do not wait for unrelated bots. |
| Claude-only company project, unavailable GPT preference, unnamed council | Filter by project permission first. Use eligible independent Claude perspectives if available; otherwise report unavailable review capability. |

This is a local fixture and decision dry-run, not an end-to-end GitHub pilot.
No live PR was opened, pushed, watched, queued, merged, or otherwise modified.
Laptop sleep recovery and real provider/watcher operation remain to be observed
on the first authorized live task. Installation tests do not prove those host
behaviors. The current conversation's loaded skill list may remain stale until
restart.

Octopus retirement covers the council and delivery uses identified in this
conversation. Its full research, scheduling, factory, and other feature set is
not reimplemented. Existing research-lab, ideate, process-lab, and specialist
plugins remain; Octopus source and data are preserved for rollback.
