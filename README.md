Backup of config stuff.

## Shared agent config

`agents/` is the tool-agnostic source of truth for coding-agent global
instructions (`AGENTS.md`) and skills (`skills/`, SKILL.md format).
Tool-specific dirs point here:

```
agents/ in this repo    consumers
--------------------    ---------
AGENTS.md        <--- @import ------ claude/CLAUDE.md   (shim: import + Claude Code-specific bits)
                 <--- symlink ------ ~/.codex/AGENTS.md
claude/CLAUDE.md <--- symlink ------ ~/.claude/CLAUDE.md
claude/settings.json <- symlink ---- ~/.claude/settings.json
skills/          <--- symlink ------ ~/.claude/skills
skills/<name>/   <--- symlink ------ ~/.agents/skills/<name>  (Codex; per skill, see below)
```

- Claude Code doesn't read AGENTS.md natively; `~/.claude/CLAUDE.md` imports it
  via `@/path` syntax and keeps Claude-specific instructions below the import.
- Tools that write new skills into `~/.claude/skills/` land them in this repo;
  review and commit or discard.
- Codex links each owned skill by hand: `ln -s <repo>/agents/skills/<name> ~/.agents/skills/`.
  A whole-dir link would also expose `skills/synced/` (Claude Code's cache of
  claude.ai account skills), which depend on Claude-only tools.
- Keep tool-specific instructions out of `AGENTS.md`; they belong in each
  tool's shim file.
- This repo is public. Keep secrets (API keys, tokens, `env` values) out of
  `claude/settings.json`.
