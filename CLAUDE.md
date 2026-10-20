@AGENTS.md

Claude-only notes:
- Phase 1: foundation + guardrails only. No skills, agents, slash commands or plugins.
- Do not add hooks or permissions to this repo's `.claude/settings.json`.
- Prefer `rg`/Grep and Read over shelling out; stdlib Python for scripts.
- When classifying mxcli commands, UNVERIFIED → treat as WRITE.
