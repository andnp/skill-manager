---
name: gitbutler
description: "Commit, push, branch, and manage version control with GitButler. Use for: commit my changes, check what changed, create a PR, push my branch, view diff, create branches, stage files, edit commit history, squash commits, amend commits, undo commits, pull requests, merge, apply and unapply branches. Replaces git - use 'but' instead of git commit, git status, git push, git checkout, git add, git diff, git branch, git rebase, git merge. Covers all git, version control, and source control operations."
---

# GitButler CLI Skill

Use GitButler CLI (`but`) only in repositories already managed by GitButler.
In an ordinary Git repository, use the repository's normal Git workflow instead.

## Applicability

Before a GitButler mutation, run `but status -fv` to confirm the workspace and obtain current IDs.
If the repository is not a GitButler workspace, stop using this skill and use Git instead.

GitButler manages multiple branches in parallel on a `gitbutler/workspace` branch.
Its workspace state and ordinary Git commit history are not interchangeable.

## Non-Negotiable Rules

1. Use `but` for GitButler write operations. Do not use `git add`, `git commit`, `git push`, `git checkout`, `git merge`, `git rebase`, `git stash`, or `git cherry-pick` to modify a GitButler workspace.
2. Read-only Git inspection is allowed when it helps explain repository history.
3. After mutations, read the returned output for the updated workspace state.
4. Use CLI IDs from `but status -fv` / `but diff` / `but show`; never hardcode IDs.
5. Create a branch for new work with `but branch new <name>` when needed.
6. When in doubt, ask the user. Never experiment with destructive commands.

## Command Patterns

- Commit: `but commit <branch> -m "<msg>" --changes <id>,<id>`
- `but commit -a` is accepted as a no-op compatibility flag; GitButler already includes uncommitted changes by default.
- Commit + create branch: `but commit <branch> -c -m "<msg>" --changes <id>`
- Amend: `but amend <file-id> <commit-id>`
- Reorder commits: `but move <source-commit-id> <target-commit-id>` (**commit IDs**, not branch names)
- Stack branches: `but move <branch-name-or-id> <target-branch-name-or-id>` (**branch names or branch CLI IDs**)
- Tear off a branch: `but move <branch-name-or-id> zz` (`zz` = unassigned)
- Push: `but push <branch-name>` — always specify the branch; never run bare `but push`.
  For a stacked set of branches, push the topmost branch in the stack, even when only
  a lower branch changed — pushing a lower branch alone has produced an incomplete or
  incorrect push of that branch's own commits. Before pushing, confirm with `but status -fv`
  or `but show <branch-id>` that the branch's lane actually contains the expected commit;
  `but push` reads GitButler's internal branch model and can silently discard a commit
  that was added outside it (e.g. via a linked worktree).
- Pull: `but pull --check` then `but pull`

## Gotchas

### Stacking branches

To stack one branch on another: `but move feature/frontend feature/backend`

**Never** use `uncommit` + `branch delete` + `branch new -a` — git branch names persist after `but branch delete`, so this approach fails. Always use `but move <branch> <target-branch>`.

To unstack: `but move feature/logging zz`. Do NOT use `but undo` to unstack — it may revert commits.

### Stacked dependency / commit-lock

Symptom: `but commit` succeeds but the file still appears in `unassignedChanges`.

Recovery:
1. `but status -fv` — find which branch originally owns the file.
2. `but move <your-branch> <dependency-branch>` — stack your branch on it.
3. `but status -fv` — file should now be assignable. Commit it.

If `but move` fails, re-run `but status -fv` and retry with exact branch names from output. Do NOT try `uncommit`, `squash`, or `undo` as workarounds.

### Conflict resolution after reorder/move

**Never** use `git add`, `git commit`, `git checkout --theirs/--ours`, or any git write commands during resolution.

1. `but status -fv` — find conflicted commits.
2. `but resolve <commit-id>` — enter resolution mode (adds conflict markers to files).
3. Edit files to remove `<<<<<<<` / `=======` / `>>>>>>>` markers.
4. `but resolve finish` — do NOT run this before editing files.
5. Repeat for remaining conflicted commits.

### Commit or pick reports success but the change doesn't persist

If `but commit --changes` or `but pick` prints a success line but `but show <id>` can't
find the commit, or `but status -fv` doesn't show it in the branch's lane, don't trust the
success message. Try `but rub <file-or-hunk-id> <existing-commit-id>` to amend the change
directly into an existing commit instead of creating a new one.

Only use `but rub` against the **topmost** commit of a branch. Amending the tip of a
non-topmost branch in a stack can unapply that branch's lane even though `but show`
confirms the content landed; recover with `but undo` or `but oplog restore` if this happens.

## Git-to-But Map

| git | but |
|---|---|
| `git status` | `but status -fv` |
| `git add` + `git commit` | `but commit ... --changes ...` |
| `git checkout -b` | `but branch new <name>` |
| `git push` | `but push <branch-name>` |
| `git rebase -i` | `but move`, `but squash`, `but reword` |
| `git rebase --onto` | `but move <branch> <new-base>` |
| `git cherry-pick` | `but pick` |

## Notes

- `--changes` accepts comma-separated values (`--changes a1,b2`) or repeated flags, not space-separated.
- Read-only git inspection (`git log`, `git blame`, `git show --stat`) is allowed.
- Don't run a redundant `but status -fv` after a mutation unless you need new IDs.
- Use `but show <branch-id>` for per-commit file changes and line counts (`but status` doesn't include these).
- Avoid `--help` probes; use this skill and `references/reference.md` first.
- Run `but skill check` only when command behavior diverges from this skill.
- For command syntax and flags: `references/reference.md`
- For workspace model: `references/concepts.md`
- For workflow examples: `references/examples.md`
