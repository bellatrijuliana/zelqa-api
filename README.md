# Zelqa API

> Flask backend for Zelqa — an AI-powered QA lifecycle management platform.

Zelqa API is the backend engine that powers test case generation, risk assessment, defect management, and traceability — all running locally with a Groq LLM. No data leaves your environment.

---

## Tech Stack

- **Python** + **Flask** — REST API
- **Supabase** (PostgreSQL) — database
- **Groq API** — LLM inference (Llama 3.3)
- **supabase-py**, **flask-cors**, **python-dotenv**

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/zelqa-api.git
cd zelqa-api
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up environment variables

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

```env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key
GROQ_API_KEY=your-groq-api-key
FLASK_SECRET_KEY=your-random-secret-key
```

> ⚠️ Never commit your `.env` file. It's already in `.gitignore`.

**Where to get these:**
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` → Supabase dashboard → Settings → API Keys → Legacy service_role key
- `GROQ_API_KEY` → [console.groq.com](https://console.groq.com) → API Keys → Create new key
- `FLASK_SECRET_KEY` → any random string

### 4. Set up the database

Run the SQL schema in your Supabase project's SQL Editor. The schema file is available in the `/docs` folder of the [zelqa-web](https://github.com/your-username/zelqa-web) repository.

### 5. Run the server

```bash
python run.py
```

The API will be available at `http://localhost:5000`.

Test the connection:

```bash
curl http://localhost:5000/api/health
```

Expected response:
```json
{ "status": "ok", "message": "Zelqa API is running" }
```

---

## Project Structure

```
zelqa-api/
├── app/
│   ├── __init__.py         ← Flask app factory + Supabase init
│   ├── config.py           ← Configuration (model, thresholds, limits)
│   ├── middleware.py       ← Auth middleware (Supabase JWT)
│   ├── routes/
│   │   ├── projects.py     ← Project CRUD
│   │   ├── features.py     ← Feature management
│   │   ├── test_cases.py   ← Test case generation + status
│   │   ├── execution.py    ← Execution log
│   │   ├── defects.py      ← Defect management + timeline
│   │   ├── rtm.py          ← Requirements traceability
│   │   ├── reports.py      ← Report metadata
│   │   └── test_plans.py   ← Test plan CRUD
│   └── services/
│       └── llm.py          ← Groq LLM wrapper
├── run.py
├── requirements.txt
└── .env.example
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Health check |
| GET/POST | `/api/projects/` | List / create projects |
| GET/PATCH/DELETE | `/api/projects/:id` | Get / update / delete project |
| GET/POST | `/api/features/:projectId` | List / create features |
| GET | `/api/test-cases/:projectId` | List test cases |
| POST | `/api/test-cases/generate` | Generate test cases via LLM |
| PATCH | `/api/test-cases/:id/status` | Approve / reject test case |
| GET/POST | `/api/execution/:projectId` | List / log execution results |
| GET/POST | `/api/defects/:projectId` | List / create defects |
| GET | `/api/defects/:projectId/stats` | Defect statistics |
| PATCH | `/api/defects/:id/status` | Update defect status |
| GET | `/api/defects/:id/timeline` | Defect status history |
| GET/POST | `/api/rtm/:projectId` | RTM links |
| GET/POST | `/api/test-plans/:projectId` | Test plans |
| PATCH | `/api/test-plans/:id` | Update test plan |

---

## Configuration

All settings are in `app/config.py`:

```python
GROQ_MODEL = 'llama-3.3-70b-versatile'  # Change to any supported Groq model

RISK_THRESHOLD = {
    'critical': 20,   # score >= 20
    'high':     12,   # score >= 12
    'medium':    6,   # score >= 6
}

MAX_GENERATED_CASES = 15  # Max test cases per generation
```

---

## Related

- [zelqa-web](https://github.com/bellatrijuliana/zelqa-web) — React frontend

---

## License

MIT