---
name: "git-automator"
description: "Automates Git workflows including init, commit, and push. Invoke when user wants to submit code, sync changes, or manage git repositories."
---

# Git Automator Skill

This skill automates standard Git workflows to ensure consistent and safe code submission.

## Capabilities

1.  **Smart Initialization**: Checks if a repo exists; if not, initializes it.
2.  **Remote Management**: Handles adding or updating remote origins.
3.  **Safe Commits**: Checks status, stages files, and commits with descriptive messages.
4.  **Push Automation**: Pushes to the correct branch, handling upstream setting.

## Usage Instructions

When the user asks to "submit code", "push changes", or "setup git":

1.  **Check Status**: Always run `git status` first to understand the current state.
2.  **Initialize (if needed)**:
    -   If not a git repo, run `git init`.
    -   If remote is provided, run `git remote add origin <url>`.
3.  **Stage & Commit**:
    -   Use `git add .` (or specific files if requested).
    -   Use `git commit -m "<message>"`. If no message provided, generate a concise one based on changes.
4.  **Push**:
    -   Use `git push -u origin main` (or appropriate branch).
    -   Handle errors like "remote origin already exists" or "upstream not set" gracefully.

## Best Practices

-   **Verify before Push**: Ensure `.gitignore` is respected.
-   **Meaningful Messages**: Commit messages should describe *what* changed and *why*.
-   **Branch Awareness**: Default to `main` or `master`, but respect existing branch names.
-   **Error Handling**: If a command fails (e.g., merge conflict), stop and report to the user.

## Example Workflow

```bash
# 1. Check status
git status

# 2. Add files
git add .

# 3. Commit
git commit -m "feat: implement new login screen"

# 4. Push
git push
```
