# Pulse

Pulse — full-stack entertainment platform: movies, books, music, events, AI assistant, and admin-only Cinema mirrors (HDRezka + AnimeVost).

## Project structure

- `backend/` — Flask API + SQLite + static web app served from `backend/static/index.html`
- `frontend/` — separate React/Vite source (development workspace)
- `start.bat` / `start.sh` — local startup scripts

## What is safe to upload to GitHub

Upload the full project root. Sensitive and runtime files are excluded by `.gitignore`:

- `.env` files
- databases (`*.db`)
- logs
- `node_modules`
- `.claude` local settings

## Local run

```bash
cd backend
pip install -r requirements.txt
python app.py
```

App runs on `http://localhost:5000`.

## Railway deploy

This repo is prepared for Railway:

- root `requirements.txt` points to `backend/requirements.txt`
- `Procfile` uses: `python backend/app.py`
- app reads `PORT` automatically

### Required env vars on Railway

- `SECRET_KEY`
- `JWT_SECRET_KEY`

### Optional env vars (recommended)

- `KINOPOISK_API_KEY`
- `GOOGLE_BOOKS_API_KEY`
- `GOOGLE_API_KEY`
- `CORS_ORIGINS` (set your Railway domain here)

Example `CORS_ORIGINS`:

```text
https://your-app.up.railway.app,http://localhost:5000,http://127.0.0.1:5000
```
