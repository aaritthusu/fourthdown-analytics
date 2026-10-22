# FourthDown Analytics — Deployment notes

Deploy as two applications if desired: **FastAPI API** + **Next.js frontend**. You can also run both on localhost indefinitely without paying for hosting.

## FastAPI service (Render, Railway, Fly.io, VM, or your machine)

Choose a provider that supports Python or a Docker image. Point its service root to the project root (`fourthdown-analytics/`), and set:

```text
Install: pip install -r requirements.txt
Start:   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
Health:  /api/health
```

On Windows PowerShell, Bash syntax for `$PORT` is not interchangeable; configure the host's service settings or use the included Dockerfile with port 8000. Free tiers and usage limits change; check the provider's current pricing rather than assuming a particular plan is free.

The committed demo artifact and CSV allow a first start with no runtime source-download dependency. For serious usage, **refresh and retrain on a machine with internet access first** and deploy the new `data/nfl_games.csv` and `artifacts/` files together. Ephemeral filesystem services will lose unpersisted caches at restart. Do not expose public training endpoints; training remains an offline CLI process.

## Frontend service (Vercel, Netlify, or Node host)

- Deploy `frontend/` as the root folder of a separate app.
- Framework: Next.js; Node 20+.
- Build command: `npm run build`.
- Set environment variable **`NEXT_PUBLIC_API_BASE_URL=https://YOUR-API-HOST.example`** without a trailing slash, then redeploy.
- Serve backend via HTTPS. Browsers will reject `https://` frontend -> `http://` API mixed content.
- For an API hosted on another domain, update the `allow_origins` list in `backend/main.py` to include the exact frontend HTTPS origin, not `*`, then redeploy.

## Docker backend

```bash
docker build -f Dockerfile.backend -t fourthdown-api .
docker run --rm -p 8000:8000 fourthdown-api
```

Visit `http://localhost:8000/docs`. The Docker image uses the bundled (partial) artifact until a refreshed cache and model are included in the image.

## Security and data maintenance

- Do not expose filesystem writes, arbitrary model files, or untrusted pickle/joblib uploads to users. `joblib` must only load artifacts created by your own training process.
- Validate third-party CSV schemas before using data, and review publisher licensing before redistributing full downloaded datasets.
- Confirm model artifacts correspond to the current cached schedule; always refresh **before** training, then deploy data/model together.
- Schedule refreshes only within source rate limits. Backtesting may change as source corrections arrive; retain dated experiment outputs if you need auditability.
- Predictions are uncertain sports-analysis estimates, not decision or betting advice.
