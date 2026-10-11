FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app
COPY pyproject.toml README.md ./
COPY sanskrit_interpreter ./sanskrit_interpreter
RUN pip install --no-cache-dir . && useradd --create-home --uid 10001 appuser

USER appuser
EXPOSE 8080
CMD ["python", "-m", "sanskrit_interpreter", "--web", "--host", "0.0.0.0", "--port", "8080"]
