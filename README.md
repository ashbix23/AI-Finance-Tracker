# AI-Finance-Tracker

An AI-powered personal finance tracker built with FastAPI and Claude. Logs transactions, auto-categorizes spending, detects habits over time, and generates natural language financial insights via a REST API.

## Stack

- **Claude (claude-sonnet-4-5)** — transaction categorization and insight generation via tool-calling
- **FastAPI** — REST API with automatic Swagger docs
- **SQLite** — local transaction storage
- **Pydantic** — request/response validation
- **Python-dotenv** — environment configuration

## Project Structure

```
ai-finance-tracker/
├── api/
│   ├── main.py                  # FastAPI app + router registration
│   ├── models.py                # Pydantic request/response schemas
│   ├── database.py              # SQLite setup + session management
│   └── routes/
│       ├── transactions.py      # POST/GET /transactions endpoints
│       ├── categories.py        # GET /categories endpoint
│       └── insights.py          # GET /insights — AI-generated summaries
├── agent/
│   ├── finance_agent.py         # Core Claude agent with tool-calling loop
│   ├── tools.py                 # Agent tools: query_transactions, get_spending_trend
│   └── memory.py                # Spending habit memory (JSON persistence)
├── prompts/
│   ├── loader.py
│   ├── categorize.txt
│   ├── insights.txt
│   └── habit_summary.txt
├── scripts/
│   └── seed_data.py             # Seeds DB with sample transactions for demo
├── data/                        # SQLite database and habits memory (gitignored)
├── main.py                      # CLI entry point
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

**1. Clone and enter the project directory:**

```bash
git clone https://github.com/ashbix23/AI-Finance-Tracker.git
cd AI-Finance-Tracker
```

**2. Create and activate a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate
```

**3. Install dependencies:**

```bash
pip install -r requirements.txt
```

**4. Configure environment variables:**

```bash
cp .env.example .env
```

Open `.env` and add your Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your API key from [console.anthropic.com](https://console.anthropic.com).

**5. Seed sample data:**

```bash
python scripts/seed_data.py
```

This creates 3 months of realistic transactions across 8 spending categories.

**6. Start the server:**

```bash
uvicorn api.main:app --reload
```

API runs at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

## API Endpoints

### Transactions

```
POST   /transactions              # Add a transaction (auto-categorized if no category passed)
GET    /transactions              # List transactions with optional filters
GET    /transactions/{id}         # Get a single transaction
DELETE /transactions/{id}         # Delete a transaction
```

Query params for `GET /transactions`: `category`, `start_date`, `end_date`, `limit`, `offset`.

### Categories

```
GET    /categories                # List all categories
GET    /categories/{name}         # Get a single category
GET    /categories/{name}/summary # Spending stats for a category over N days
```

### Insights

```
POST   /insights                  # AI-generated spending analysis
GET    /insights/summary          # Fast category breakdown (no AI call)
```

## Usage

**Add a transaction — Claude auto-categorizes it:**

```bash
curl -X POST http://localhost:8000/transactions \
  -H "Content-Type: application/json" \
  -d '{"amount": 12.50, "description": "Chipotle", "date": "2026-04-15"}'
```

**Generate an AI insight report:**

```bash
curl -X POST http://localhost:8000/insights \
  -H "Content-Type: application/json" \
  -d '{"period_days": 30}'
```

**Focus the insight on a specific area:**

```bash
curl -X POST http://localhost:8000/insights \
  -H "Content-Type: application/json" \
  -d '{"period_days": 30, "focus": "subscriptions"}'
```

**CLI usage:**

```bash
python main.py habits
python main.py ask "how much did I spend on food last month?"
python main.py ask "what are my biggest expenses this week?"
```

## How It Works

**Auto-categorization:** Every transaction posted without a category is passed to Claude with a zero-shot prompt. Claude returns a single category label from the fixed list. No embeddings, no classifiers — just a direct prompt with `max_tokens: 64`.

**Insight generation:** The `/insights` endpoint passes the full transaction list, category breakdown, and accumulated habit memory to Claude in a single prompt. Claude can call tools mid-generation — `get_spending_trend` to compare periods, `query_transactions` to drill into specific categories — before writing the final narrative.

**Habit memory:** After each insight generation, `memory.py` updates a local `habits.json` with rolling category averages, exponentially weighted spend scores, and trend detection. Any category that shifts more than 15% from its historical average gets flagged. This memory is injected into every subsequent insight prompt so Claude always has longitudinal context.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | — | Required. Get from console.anthropic.com |
| `FINANCE_MODEL` | `claude-sonnet-4-5` | Claude model to use |
| `DB_PATH` | `data/finance.db` | SQLite database path |
| `MEMORY_PATH` | `data/habits.json` | Habit memory file path |
