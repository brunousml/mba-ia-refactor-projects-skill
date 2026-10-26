#!/bin/bash
# Executa a refactor-arch (Fases 1-2 e depois Fase 3) em modo headless num projeto.
# Uso: scripts/run-skill.sh <dir-projeto> <relatorio> <dir-logs>
set -u
cd "$1"
OPTS=(--add-dir ../reports --add-dir ../docs --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash Agent Skill")
claude -p "/refactor-arch $2" "${OPTS[@]}" > "$3/phase-1-2.log" 2>&1
claude -p --continue "sim, prossiga com a Fase 3" "${OPTS[@]}" > "$3/phase-3.log" 2>&1
echo "exit=$?" >> "$3/phase-3.log"
