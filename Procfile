# Procfile for Railway deployment
web: alembic upgrade head && uvicorn server_fastapi.main:app --host 0.0.0.0 --port $PORT
worker: celery -A server_fastapi.celery_app worker --loglevel=info --concurrency=2
beat: celery -A server_fastapi.celery_app beat --loglevel=info
