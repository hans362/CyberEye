#!/bin/bash
if [ "$ROLE" = "server" ]; then
  sleep 10
  fastapi run main.py --port 8000
elif [ "$ROLE" = "scheduler" ]; then
  sleep 20
  python3 scheduler.py
elif [ "$ROLE" = "worker" ]; then
  sleep 20
  python3 worker.py
else
  echo "Unknown role: $ROLE"
  exit 1
fi
