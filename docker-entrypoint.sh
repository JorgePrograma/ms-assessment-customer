#!/bin/sh
set -e

# Apply pending database migrations before starting the API.
alembic upgrade head

exec "$@"
