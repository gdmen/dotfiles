Backup of config stuff.

## Shared agent config

`AGENTS.md` and `skills/` are the tool-agnostic source of truth for coding-agent
global instructions and skills (SKILL.md format). Tool-specific dirs point here:

```
this repo                      consumers
---------                      ---------
AGENTS.md        <--- @import ------ claude/CLAUDE.md   (shim: import + Claude Code-specific bits)
                 <--- symlink ------ ~/.codex/AGENTS.md
claude/CLAUDE.md <--- symlink ------ ~/.claude/CLAUDE.md
skills/          <--- symlink ------ ~/.claude/skills
```

- Claude Code doesn't read AGENTS.md natively; `~/.claude/CLAUDE.md` imports it
  via `@/path` syntax and keeps Claude-specific instructions below the import.
- Tools that write new skills into `~/.claude/skills/` land them in this repo;
  review and commit or discard.
- Keep tool-specific instructions out of `AGENTS.md`; they belong in each
  tool's shim file.
