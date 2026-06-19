# Deployment guide

## Local Docker deployment

1. Copy `.env.example` to `.env` and replace `SECRET_KEY`.
2. Add `OPENAI_API_KEY` to enable model-written synthesis. The system remains functional without it.
3. Keep `MARKET_DATA_MODE=demo` for reproducible evaluation, or use `live` for the yfinance adapter.
4. Run `docker compose up --build -d`.
5. Open the dashboard on `http://localhost:8501`, API docs on `http://localhost:8000/docs`, and Prometheus on `http://localhost:9090`.

## Production checklist

- Put the API behind TLS and a managed ingress; do not expose PostgreSQL or Redis publicly.
- Store secrets in the platform secret manager and rotate the JWT signing key.
- Replace `Base.metadata.create_all` with reviewed Alembic migrations in the release pipeline.
- Use managed PostgreSQL with PITR, managed Redis with TLS/auth, persistent Chroma storage (or a supported vector service), and encrypted backups.
- Replace demo/yfinance data with licensed, point-in-time providers and honor redistribution terms.
- Add rate limiting, refresh-token rotation or an external identity provider, audit retention, vulnerability scanning and a WAF.
- Run model/prompt evaluations, adversarial-input tests, human compliance review and recommendation suitability controls.
- Pin container images by digest and use a non-root runtime (already configured).
- Scale API workers horizontally; move long research runs to a task queue for high traffic.

The supplied CI workflow lints, tests with coverage, and builds the container. A deployment job should consume the immutable image only after environment-specific approval.

