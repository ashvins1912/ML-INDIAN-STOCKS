# Indian Quant Market Intelligence — scaffold

Dockerized foundation for an NSE equities / mutual-fund research platform with broker adapters, FastAPI, Streamlit, Airflow, PostgreSQL, Redis, and InfluxDB.

## Run
1. Copy `.env.example` to `.env` and replace passwords/tokens. Generate Fernet keys:
   ```bash
   python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
   ```
   Set `FERNET_KEY` to that key and set `AIRFLOW_FERNET_KEY` to a valid Airflow Fernet key (generate using `airflow config get-value core fernet_key` or the Airflow utility).
2. `docker compose up --build -d`
3. Open Streamlit at http://localhost:8501, FastAPI docs at http://localhost:8000/docs, Airflow at http://localhost:8080.

Airflow may need database initialization and a local admin account. For a fresh deployment run:
```bash
docker compose run --rm airflow-webserver airflow db migrate
docker compose run --rm airflow-webserver airflow users create --username admin --password admin --firstname Admin --lastname Quant --role Admin --email admin@example.local
```
Then start/restart webserver and scheduler. **Change the example admin password immediately.**

## APIs
- `GET /health`
- `GET /api/v1/instruments/search?q=rel`
- `POST /api/v1/instruments/sync`
- `GET /api/v1/providers`
- `GET /api/v1/market/history/RELIANCE?provider=YFINANCE&period=1y&interval=1d`
- `POST /api/v1/auth/init` with JSON `{ "provider": "ZERODHA", "user_id": "local-user" }` (state only; broker authorization/token exchange must be configured)

## Status / limitations (read before production)
- This is a runnable **scaffold**, not an investment-ready or fully credentialed platform. YFinance historical retrieval is implemented. Broker adapter classes are extension points and currently require API entitlement/session exchange implementation.
- Provider instrument masters change format and access behavior. Sync is best-effort, reports errors/coverage, and does **not fabricate tokens**. The strict requested acceptance test (all four broker tokens populated on every stock) is impossible for cross-provider coverage and should be replaced with coverage assertions.
- OAuth routes validate Redis state but token exchange, callback registration, and provider-specific authorization URLs are not implemented. They intentionally do not store raw callback codes as access tokens.
- NSE Bhavcopy downloading/reconciliation is a safe stub; implement and verify current official endpoints before allowing corrections to overwrite market records.
- MFapi.in NAV fetching is not wired yet. Mutual fund history/modeling needs its own NAV feature and target pipeline, not stock OHLCV features.
- Feature calculations are implemented; supervised target helper is present. The ML utilities are baseline only. Temporal folds, Optuna tuning, isotonic calibration, model registry, production-grade champion/challenger checks, mature outcome grading, and 30-trade precision force-retrain policy require full dataset wiring and should not be enabled without reliable data.
- InfluxDB provisioning is configured, but the market-data write/read repository is not wired. Historical candles currently come directly from YFinance in the API.
- Docker Compose defines 7 long-running services (Postgres, Redis, Influx, Airflow webserver, Airflow scheduler, API, Dashboard), plus an optional one-off Airflow init command; “six containers” in the original brief is inconsistent with its listed components.
- This dashboard does not emit trade recommendations; it is for data/ML research. Prediction KPIs are deliberately not invented.

## Data and security
- Never commit `.env`; it contains secret material.
- Redis sessions are encrypted with Fernet and capped at 12 hours. Session persistence refuses to run without a configured key.
- Set OAuth redirect URIs to your deployed frontend and use HTTPS in production.
- Add authentication, authorization, rate limiting, TLS, secrets management, audit logging, and backups before exposing services.

## Tests
Install Python dependencies and run:
```bash
pip install -r requirements.txt
pytest -q
```
