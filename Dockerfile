FROM python:3.12-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /app
RUN addgroup --system finagent && adduser --system --ingroup finagent finagent
COPY pyproject.toml requirements.txt ./
COPY finagent ./finagent
RUN pip install --upgrade pip && pip install .
RUN mkdir -p /app/data && chown -R finagent:finagent /app
USER finagent
EXPOSE 8000
CMD ["uvicorn", "finagent.api.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]

