# NetPulse

NetPulse is an ISP-focused destination monitoring platform with:

- continuous probes (latency/loss/jitter)
- incident detection and lifecycle tracking
- automatic trace capture hooks
- Telegram alert integration
- realtime-ready API and dark NOC dashboard frontend

## Current Implementation Scope

This first build includes:

- Flask + SQLite backend (`backend/`)
- APScheduler-driven monitoring loop
- incident detection rules (latency, packet loss, down, recovery)
- Telegram notifier with delivery logs
- trace runner service (`mtr -r -c 10 target`)
- REST APIs for probes, results, incidents, KPI summary, and source assignment
- React + Vite + Tailwind frontend (`frontend/`) with KPI cards, probe table, active incidents, and latency trend chart

## Project Structure

```bash
backend/
  app.py
  models.py
  monitor.py
  telegram.py
  traceroute.py
  websocket.py
frontend/
  src/
    api/
    charts/
    components/
    hooks/
```

## Run Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Backend URL: `http://localhost:5000`

## Run Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend URL: `http://localhost:5173`

## Run With Docker Compose

1) Configure backend credentials in `backend/.env` (especially `BOT_TOKEN` and `CHAT_ID`).

2) Build and start:

```bash
docker compose up --build -d
```

3) Open:

- frontend: `http://localhost:5173`
- backend health: `http://localhost:5000/api/health`

4) View logs:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

5) Stop:

```bash
docker compose down
```

## Environment

Copy `.env.example` to `.env` and update as needed:

- `BOT_TOKEN`
- `CHAT_ID`
- `DATABASE_URL`
- monitor tuning values

## Next Steps

- replace polling with websocket subscription in frontend
- add target detail page with range selectors (15m/1h/24h/7d)
- add incident center pages (active/resolved)
- implement aggregated retention jobs (hourly rollups)
- add auth and role-based admin controls
# netpulse
