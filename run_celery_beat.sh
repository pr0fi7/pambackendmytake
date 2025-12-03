#!/usr/bin/env bash
uv run celery -A app.celery_app beat \
    -S app.celery_db_scheduler.DatabaseScheduler \
    --loglevel=DEBUG \
    --max-interval=10


