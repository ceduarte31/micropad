#!/usr/bin/env bash
set -e

# Ensure writable directories exist for mounted volumes
mkdir -p /app/.generated/micropad/vectordb \
         /app/.generated/micropad/model_cache \
         /app/.generated/micropad/detection_results \
         /app/.generated/micropad/logs \
         /app/.generated/micropad/conversations

# Fix ownership for the app user
chown -R micropad:micropad /app/.generated /home/micropad

# Default to bash if no command is provided
if [ $# -eq 0 ]; then
  set -- bash
fi

# Drop privileges and run the requested command
# Preserve PATH and PYTHONPATH for the micropad user
exec su -s /bin/bash micropad -c "export PATH=/home/micropad/.local/bin:\$PATH && export PYTHONPATH=/app/src:\$PYTHONPATH && cd /app && exec $*"
