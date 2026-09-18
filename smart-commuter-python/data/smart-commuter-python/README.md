# Smart Commuter Companion — Python/FastAPI

Python conversion of the Rachel-first commuter companion. The browser UI remains HTML/CSS/JavaScript; all server-side API, routing, disruption and recommendation logic is Python.

## Run

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # optional: add LTA_ACCOUNT_KEY for live DataMall feeds
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Open http://127.0.0.1:8000

The replay scenarios work without a DataMall key. Choose **East West Line signalling fault** in the app to demonstrate rerouting. Replayed data is explicitly labelled simulated.

## Structure

- `main.py` FastAPI server and `/api/brief` pipeline
- `app/router.py` Python Dijkstra route planner
- `app/advice.py` Python recommendation/interrupt rules
- `app/sources.py` LTA DataMall + data.gov.sg clients
- `app/lines.py` canonical line-code mapping
- `app/personas.py` persona configuration
- `app/network.py` focused EWL/DTL demo graph
- `public/` existing mobile UI
- `data/replay/` injected, labelled demo disruptions

## Important limitation

The rail graph is deliberately focused on Rachel's east-to-city journey and its DTL alternative. It is not a full Singapore routing engine. The frontend uses OpenStreetMap tiles for the demo; use a suitable keyed/self-hosted tile source before real traffic.
