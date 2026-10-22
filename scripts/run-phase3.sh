#!/bin/bash
# Retoma a sessão da refactor-arch do projeto e executa só a Fase 3.
# Uso: scripts/run-phase3.sh <dir-projeto> <dir-logs>
set -u
cd "$1"
claude -p --continue "sim, prossiga com a Fase 3" --add-dir ../reports --add-dir ../docs \
  --permission-mode acceptEdits --allowedTools "Read Glob Grep Write Edit Bash Agent" > "$2/phase-3.log" 2>&1
echo "exit=$?" >> "$2/phase-3.log"
