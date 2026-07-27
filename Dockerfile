FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=config.settings

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Static (suite-launcher.js etc.) — never needs the DB.
RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
# Render/most hosts inject $PORT; default to 8000 locally.
CMD gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 120
