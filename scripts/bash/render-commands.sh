#!/usr/bin/env bash
# Render the /sdd-* commands for Copilot, Cursor, Codex and Gemini from .claude/skills/sdd-*/SKILL.md.
# Usage: render-commands.sh [--check]     (thin wrapper around scripts/python/render_commands.py; ADR-0091)
set -e
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$SCRIPT_DIR/../python/render_commands.py" "${1:---render}"
