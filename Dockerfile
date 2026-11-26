FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gettext \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.12.11 /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen --no-dev

COPY . .

RUN msgfmt locale/fr/LC_MESSAGES/django.po \
    -o locale/fr/LC_MESSAGES/django.mo

WORKDIR /app/src

RUN DJANGO_SECRET_KEY=build-only-not-for-runtime \
    DATASOURCE_ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')" \
    OPENAI_API_KEY=build-only-not-for-runtime \
    DATABASE_URL=sqlite:////tmp/askmydata-build.sqlite3 \
    python manage.py collectstatic --noinput

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
