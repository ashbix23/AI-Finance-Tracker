from fastapi import FastAPI
from contextlib import asynccontextmanager
from api.database import init_db
from api.routes import transactions, categories, insights


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="AI Finance Tracker",
    description="Track spending, detect habits, and generate AI-powered insights.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(insights.router, prefix="/insights", tags=["insights"])


@app.get("/")
def root():
    return {
        "name": "AI Finance Tracker",
        "version": "1.0.0",
        "endpoints": [
            "/transactions",
            "/categories",
            "/insights",
            "/docs",
        ],
    }
