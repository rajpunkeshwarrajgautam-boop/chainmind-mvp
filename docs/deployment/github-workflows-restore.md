# Restore GitHub Actions (after `workflow` scope)

The first `git push` failed because the GitHub OAuth token used by `gh` did not include the **`workflow`** scope. Workflows were temporarily removed so the repository could be created and pushed.

## Option A — refresh `gh` (recommended)

1. Run:

   ```powershell
   gh auth refresh -h github.com -s workflow
   ```

2. Restore workflow files from the commit **before** they were removed:

   ```powershell
   cd "D:\ai company\chainmind-mvp"
   git checkout a332247 -- .github/workflows
   git commit -m "ci: restore GitHub Actions workflows"
   git push
   ```

## Option B — paste from Git history

If you prefer not to use `git checkout` from an old commit, open the tree at commit `a332247` on GitHub and recreate `.github/workflows/ci.yml` and `.github/workflows/supply-chain.yml` manually.

## Verify

- Actions tab should show workflows on the next push to `main`.
