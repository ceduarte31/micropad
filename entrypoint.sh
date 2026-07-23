#!/usr/bin/env bash
set -e

# Ensure writable directories exist for mounted volumes
mkdir -p /app/.generated/micropad/vectordb \
         /app/.generated/micropad/model_cache \
         /app/.generated/micropad/detection_results \
         /app/.generated/micropad/logs \
         /app/.generated/micropad/conversations \
         /app/batch_results

# Fix ownership for the app user
chown -R micropad:micropad /app/.generated /home/micropad /app/batch_results

# Default to bash if no command is provided
if [ $# -eq 0 ]; then
  set -- bash
fi

# Drop privileges and run the requested command.
# Preserve PATH and PYTHONPATH for the micropad user. Each argument is
# shell-escaped (printf %q) before being joined into the su -c string, so
# arguments containing spaces/quotes/semicolons/parens (e.g. `python -c "..."`)
# survive intact instead of being re-split by the inner shell.
printf -v escaped_cmd '%q ' "$@"
exec su -s /bin/bash micropad -c "export PATH=/home/micropad/.local/bin:\$PATH && export PYTHONPATH=/app/src:\$PYTHONPATH && cd /app && exec $escaped_cmd"
