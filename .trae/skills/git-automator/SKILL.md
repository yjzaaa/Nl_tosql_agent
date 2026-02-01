---
name: "git-automator"
description: "Automates Git workflows. ONLY performs commit/push when explicitly requested by the user. Default behavior is to check status only."
---

# Git Automator Skill

This skill handles Git operations with a focus on safety and user control. It ensures that code is only submitted (committed/pushed) when the user explicitly intends to do so.

## Core Rules

1.  **No Auto-Commit**: Never automatically commit changes after editing files unless the user *explicitly* asks to "submit", "commit", or "save to git".
2.  **Check Status First**: Always run `git status` to visualize pending changes before taking action.
3.  **Explicit Push**: Do not push to remote unless the user asks to "push", "upload", "sync", or "submit to remote".

## Usage Instructions

### Scenario 1: User asks to "Check Git" or "What changed?"
1.  Run `git status`.
2.  Summarize the changed files.
3.  **STOP**. Do not add or commit.

### Scenario 2: User asks to "Commit" or "Save changes"
1.  Run `git status` to confirm what will be added.
2.  Run `git add <files>` (use `.` for all, or specific paths if requested).
3.  Run `git commit -m "<message>"`.
    -   *Requirement*: Use a descriptive commit message based on the actual changes.
4.  **STOP**. Do not push unless explicitly requested.

### Scenario 3: User asks to "Submit", "Push", or "Sync"
1.  Perform **Scenario 2** (Commit) if there are uncommitted changes.
2.  Run `git push`.
    -   Use `git push -u origin <branch>` if upstream is not set.

## Best Practices

-   **Safety First**: When in doubt, ask for confirmation before running `git push`.
-   **Granularity**: Prefer committing related changes together.
-   **Visibility**: Always show the output of `git status` or the commit hash to the user.

## Example Commands

-   User: "Update the README" -> **Agent**: Edits file. (NO Git action).
-   User: "Check changes" -> **Agent**: `git status`.
-   User: "Commit this" -> **Agent**: `git add .` + `git commit`.
-   User: "Push to github" -> **Agent**: `git push`.
