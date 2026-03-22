FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1

RUN pip install --no-cache-dir poetry

WORKDIR /app

COPY pyproject.toml ./
RUN poetry install --no-root

COPY . .
RUN poetry install

CMD ["poetry", "run", "pytest"]
