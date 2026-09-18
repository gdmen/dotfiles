@/Users/garymenezes/repositories/dotfiles/agents/AGENTS.md

## Claude Code specifics

- **Code review before commit.** Get an independent review via the in-house `/code-review` skill and apply blocking findings before committing. **Never run or offer `/codex`. I don't have it hooked up.**
- Open draft PRs via the GitHub MCP.
- Raise design questions with AskUserQuestion.

### GitHub MCP

- Write **raw** characters in issue and PR bodies (`<`, `>`, `&`, `"`, `'`). The `issue_read` tool HTML-escapes its *output*; don't mirror that escaping when composing, or the entity gets stored literally.
- Verify what's actually stored via the raw REST API or the GitHub UI, not an MCP re-read.
- For targeted edits to a large issue body, **never regenerate it from memory.** Fetch the stored body via the REST API to a file, make the change with Edit, write it back, then re-fetch and diff to confirm byte fidelity. Delegate that loop to an agent to keep the body out of the main context.
