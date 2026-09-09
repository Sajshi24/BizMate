# BizMate

AI-powered smart business assistant for small businesses and local retailers.

## Features

- **Products & Inventory** — Manage products, monitor stock levels, get restock alerts
- **Sales** — Record transactions and track revenue in real time
- **Analytics** — Sales trends, revenue trends, top products, category performance
- **Finance** — Revenue, cost, profit, and margin overview
- **Marketing Studio** — AI-generated captions, hashtags, campaigns, campaign calendars, and promotional posters
- **AI Business Advisor** — Actionable advice from Gemini AI based on your live business data

## Tech Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI (Python) |
| Database | MongoDB |
| Frontend | Streamlit |
| AI | Google Gemini 2.5 Flash |
| Image Generation | Gemini, Google Imagen, OpenAI DALL-E 3, Stability AI (auto-fallback) |

## Environment Variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

| Variable | Required | Description |
|---|---|---|
| `MONGO_URI` | Yes | MongoDB connection string |
| `DATABASE_NAME` | No | Database name (default in code: `local_logic`; recommended: `bizmate`) |
| `GEMINI_API_KEY` | Yes | Google Gemini API key — required for AI features |
| `OPENAI_API_KEY` | No | OpenAI API key — fallback for poster image generation |
| `STABILITY_API_KEY` | No | Stability AI key — fallback for poster image generation |

## Setup

### Prerequisites

- Python 3.11+
- MongoDB (local install or [MongoDB Atlas](https://www.mongodb.com/atlas))
- Google Gemini API key ([get one here](https://aistudio.google.com/app/apikey))

### Install dependencies

```bash
pip install -r requirements.txt
```

### Seed sample data (optional)

```bash
# Start the backend first, then run:
python seed.py
```

## Running

### Backend (FastAPI)

```bash
uvicorn backend.main:app --reload
```

- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs

### Frontend (Streamlit)

```bash
streamlit run frontend/dashboard.py
```

- App: http://localhost:8501

Run both commands in separate terminals from the project root.
