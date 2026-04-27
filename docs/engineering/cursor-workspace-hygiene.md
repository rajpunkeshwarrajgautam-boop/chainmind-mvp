# Cursor workspace hygiene (`.playwright-mcp`)

Some Cursor setups open a **parent folder** (for example `D:\ai company`) that contains the git repo (`chainmind-mvp/`) **and** sibling folders. The Playwright MCP browser tools may write capture files to **`.playwright-mcp/` at the workspace root** — which can sit **outside** `chainmind-mvp/` if that parent folder is the workspace.

## Policy

1. **Never commit** YAML snapshots, screenshots, or console logs from `.playwright-mcp/` — they may contain URLs, tokens in page content, or customer data from live sessions.
2. **`chainmind-mvp/.gitignore`** includes `.playwright-mcp/` so captures **inside** the repo tree are ignored if the workspace root is the repo.
3. If your workspace root is a **parent** of `chainmind-mvp/` and `.playwright-mcp/` appears next to the repo (not inside it), either:
   - open **`chainmind-mvp/`** as the Cursor workspace root, or  
   - add `.playwright-mcp/` to a **parent** `.gitignore` if that parent is its own git repo, or  
   - add the path to your **global git exclude**.

## Cleanup

Delete the folder periodically if disk noise matters; regenerating captures is cheap.
