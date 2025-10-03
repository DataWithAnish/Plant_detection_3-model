FROM python:3.10-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libgl1 libglib2.0-0 libjpeg62-turbo libpng16-16 libtiff5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements-merged.txt

ENV DJANGO_SETTINGS_MODULE=plantweb.settings
ENV PORT=8000
EXPOSE 8000

CMD ["bash", "-lc", "gunicorn plantweb.wsgi:application --bind 0.0.0.0:${PORT} --workers 2 --threads 4 --timeout 120"]
