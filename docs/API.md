# REST API

Interactive OpenAPI documentation is served at `/docs`; the machine-readable schema is at `/openapi.json`.

| Method | Path | Purpose | Auth |
|---|---|---|---|
| POST | `/api/v1/auth/signup` | Register and return a JWT | No |
| POST | `/api/v1/auth/token` | OAuth2 password login | No |
| POST | `/api/v1/research` | Run the 12-agent committee | Bearer |
| GET | `/api/v1/research` | List the caller's reports | Bearer |
| GET | `/api/v1/research/{id}/pdf` | Download a report | Bearer |
| POST | `/api/v1/portfolio/simulate` | Backtest and Monte Carlo simulation | Bearer |
| GET | `/health` | Liveness check | No |
| GET | `/metrics` | Prometheus exposition | No |

Example:

```bash
curl -s http://localhost:8000/api/v1/auth/signup \
  -H 'content-type: application/json' \
  -d '{"email":"analyst@example.com","password":"replace-with-a-long-password"}'

curl -s http://localhost:8000/api/v1/research \
  -H "authorization: Bearer $TOKEN" -H 'content-type: application/json' \
  -d '{"ticker":"AAPL","risk_profile":"moderate","horizon_years":3}'
```

Errors use FastAPI's standard `{"detail": ...}` body. Validation failures return 422, invalid credentials 401, duplicate registration 409, and missing reports 404.

