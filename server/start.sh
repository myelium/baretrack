#!/bin/sh
set -e

# Create tables and stamp alembic
python -c 'from database import engine, Base; from models import *; Base.metadata.create_all(engine)'
python -m alembic stamp head

exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
