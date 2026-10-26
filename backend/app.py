
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from search import search_podcast

from pathlib import Path
import pandas as pd
from search import chunks_df

app = FastAPI(title="Perfect Person Archive API")

# Allow the local frontend to make requests during development.
# We'll replace these with your GitHub Pages origin later.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "https://tientle.github.io",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {"message": "Perfect Person Archive API is running!"}


@app.get("/search")
def search(
    query: str = Query(min_length=1),
    top_k: int = Query(default=5, ge=1, le=20),
):
    return search_podcast(query, top_k=top_k)


@app.get("/stats")
def archive_stats():
    base_dir = Path(__file__).resolve().parent.parent

    # Total number of episodes in our playlist
    episodes = pd.read_csv(base_dir / "data" / "episodes.csv")
    total = episodes["video_id"].nunique()

    # Episodes currently included in the search index
    indexed = chunks_df["video_id"].nunique()

    return {
        "indexed_episodes": int(indexed),
        "total_episodes": int(total),
        "percentage": round(indexed / total * 100, 1)
    }
