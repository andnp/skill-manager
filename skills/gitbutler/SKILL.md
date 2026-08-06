---
name: but
version: dev
description: "Commit, push, branch, and manage version control with GitButler. Use for: commit my changes, check what changed, create a PR, push my branch, view diff, create branches, stage files, edit commit history, squash commits, amend commits, undo commits, pull requests, merge, apply and unapply branches. Replaces git - use 'but' instead of git commit, git status, git push, git checkout, git add, git diff, git branch, git rebase, git merge. Covers all git, version control, and source control operations."
author: GitButler Team
---

# GitButler CLI Skill

Use GitButler CLI (`but`) as the default version-control interface.

## UNDERSTAND WHAT GITBUTLER DOES

GitButler manages multiple branches in parallel on a single `gitbutler/workspace` branch. 
When you make changes, they exist in GitButler's internal state, NOT as real git commits yet.

- `but status -fv` shows you GitButler's view: what branches exist, what changes are staged
- Raw `git` commands show you actual git commits, which don't match GitButler's workspace state
- This mismatch causes confusion: git shows one thing, but status shows another

Using raw git to "fix" things makes it worse because:
1. GitButler can't track what you did with git
2. Your manual git operations desynchronize from GitButler's internal state
3. oplog becomes useless (it can't restore to a state it didn't track)
4. The only fix is manual user intervention

GitButler is managing your branches for you. Let it do its job.

## Non-Negotiable Rules

1. **NEVER USE RAW GIT EVER.** Not `git status`, `git log`, `git show`, `git diff`, nothing. Use `but` for everything.
2. Use `but` for all write operations. Never run `git add`, `git commit`, `git push`, `git checkout`, `git merge`, `git rebase`, `git stash`, or `git cherry-pick`. If the user says a `git` write command, translate it to `but` and run that.
3. After mutations, read the returned output for the updated workspace state.
4. Use CLI IDs from `but status -fv` / `but diff` / `but show`; never hardcode IDs.
5. Start with `but status -fv` before mutations so IDs and stack state are current.
6. Create a branch for new work with `but branch new <name>` when needed.
7. When in doubt, ask the user. Never experiment with destructive commands.

## Command Patterns

- Commit: `but commit <branch> -m "<msg>" --changes <id>,<id>`
- `but commit -a` is accepted as a no-op compatibility flag; GitButler already includes uncommitted changes by default.
- Commit + create branch: `but commit <branch> -c -m "<msg>" --changes <id>`
- Amend: `but amend <file-id> <commit-id>`
- Reorder commits: `but move <source-commit-id> <target-commit-id>` (**commit IDs**, not branch names)
- Stack branches: `but move <branch-name-or-id> <target-branch-name-or-id>` (**branch names or branch CLI IDs**)
- Tear off a branch: `but move <branch-name-or-id> zz` (`zz` = unassigned)
- Push: `but push` or `but push <branch-id>`
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

## Git-to-But Map

| git | but |
|---|---|
| `git status` | `but status -fv` |
| `git add` + `git commit` | `but commit ... --changes ...` |
| `git checkout -b` | `but branch new <name>` |
| `git push` | `but push` |
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
