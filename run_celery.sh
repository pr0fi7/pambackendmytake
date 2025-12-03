#!/usr/bin/env bash
uv run celery -A app.celery_app worker -l info -n worker1@%h

