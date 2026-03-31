#!/bin/sh
set -e

# Create tables and stamp alembic
python -c 'from database import engine, Base; from models import *; Base.metadata.create_all(engine)'
python -m alembic stamp head

# Download YouTube cookies from R2 if configured
if [ -n "$R2_ENDPOINT_URL" ] && [ -n "$R2_BUCKET_NAME" ]; then
  python -c "
import boto3, os
try:
    client = boto3.client('s3',
        endpoint_url=os.environ['R2_ENDPOINT_URL'],
        aws_access_key_id=os.environ['R2_ACCESS_KEY_ID'],
        aws_secret_access_key=os.environ['R2_SECRET_ACCESS_KEY'],
        region_name='auto')
    client.download_file(os.environ['R2_BUCKET_NAME'], 'config/cookies.txt', '/app/cookies.txt')
    print('Downloaded cookies.txt from R2')
except Exception as e:
    print(f'No cookies file: {e}')
"
fi

exec uvicorn server:app --host 0.0.0.0 --port ${PORT:-8000}
