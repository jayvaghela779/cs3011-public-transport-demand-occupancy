# Contributing

## Workflow

1. Pull the latest `main`.
2. Create a branch named after the work: `feature/<short-name>` (for example `feature/seasonal-naive-baseline`) or `fix/<short-name>`.
3. Commit small, working steps from **your own GitHub account**, with messages that say what changed and why.
4. Push the branch and open a pull request. Jay reviews and merges.

## Rules

- **Never** rewrite or backdate history on shared branches (`main` or anything already pushed). No force-pushes to `main`.
- **Never** commit secrets (API keys, tokens, `.env` files), private course material, chat exports, emails or personal details.
- **Never** commit raw SUNT files. The pipeline downloads them into `data/raw/`, which is git-ignored.
- Every number in the slides or README must come from a script in this repository, and the output it wrote must be committed.
- Code copied or adapted from elsewhere needs a licence that allows it and a comment with the source link. Repositories without a licence may be read for ideas but not copied.
- If AI tools helped write a commit, say so with a `Co-Authored-By` line or in the message.

## Before you push

```bash
pytest
```

All tests should pass. If a test fails for a reason you cannot fix, say so in the pull request.
