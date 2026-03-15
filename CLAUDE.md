# popmailmcp

## Project Rules
- Session Log is updated AUTOMATICALLY after every significant action — no manual trigger needed
- See global ~/.claude/CLAUDE.md for full protocol

## Plugin: context-mode
- `mksglu/context-mode` is installed globally for local session continuity
- It handles local memory (SQLite) automatically — no action needed
- Cross-PC memory is handled via CLAUDE.md Session Log + git push/pull
- Install on new PC: `/plugin marketplace add mksglu/context-mode` then `/plugin install context-mode@context-mode`


# Session Log

> This section is auto-maintained by Claude. Cross-PC memory via git push/pull.

### Session Memory Protocol
- Session log is updated **AUTOMATICALLY** after every significant action
- No manual "save memory" needed — sessions can die at any moment
- After updating, auto-commit ONLY CLAUDE.md with message `docs: auto-save session log`
- For cross-PC sync: just `git push` (or it syncs on next commit)

