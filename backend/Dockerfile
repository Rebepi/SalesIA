FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN groupadd --system salesia && useradd --system --gid salesia --create-home salesia
WORKDIR /app
COPY pyproject.toml ./
COPY alembic.ini ./
COPY alembic ./alembic
COPY src ./src
RUN pip install --no-cache-dir .
RUN mkdir -p /app/private_storage && chown -R salesia:salesia /app
USER salesia
EXPOSE 8000
CMD ["uvicorn", "salesia.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
