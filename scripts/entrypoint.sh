#!/bin/sh
set -eu

python /app/scripts/import_dataset.py
exec "$@"
