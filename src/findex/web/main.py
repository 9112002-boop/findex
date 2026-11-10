import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from ..models import Index
from ..search import search
from ..storage import load_pickle

logger = logging.getLogger("findex.web")


# Глобальний стан (завантажується в lifespan)
class AppState:
    def __init__(self):
        self.index: Index | None = None
        self.corpus: dict[int, str] = {}


state = AppState()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Завантаження індексу при старті
    index_path = Path("index.bin")
    if index_path.exists():
        logger.info(f"Loading index from {index_path}")
        data = load_pickle(index_path)
        state.index = Index(postings=data['postings'], doc_meta=data['doc_meta'])

        # Завантаження корпусу для сніпетів
        data_dir = Path("data")
        if data_dir.exists():
            from ..iterators import iter_documents
            for i, text in enumerate(iter_documents(data_dir)):
                state.corpus[i] = text
    else:
        logger.warning("Index not found. Service will start without index.")
    yield


app = FastAPI(lifespan=lifespan)

# Абсолютний шлях до папки з шаблонами
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# --- Моделі Pydantic ---
class SearchResultModel(BaseModel):
    doc_id: int
    score: float
    snippet: str


class SearchResponse(BaseModel):
    results: list[SearchResultModel]
    total: int
    page: int
    k: int


class StatsResponse(BaseModel):
    num_docs: int
    num_terms: int
    avg_doc_length: float


# --- Маршрути ---

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Віддає HTML-сторінку з полем пошуку."""
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


@app.get("/search", response_model=SearchResponse)
async def search_endpoint(
        q: str,
        k: int = 10,
        scorer: str = "tfidf",
        page: int = 1
):
    if not state.index:
        raise HTTPException(status_code=503, detail="Index not loaded")

    # Простий пошук
    results = search(state.index, q, scorer_type=scorer, top_k=k, corpus_dict=state.corpus)

    return SearchResponse(
        results=[
            SearchResultModel(doc_id=r.doc_id, score=r.score, snippet=r.snippet)
            for r in results
        ],
        total=len(results),
        page=page,
        k=k
    )


@app.get("/docs/{doc_id}")
async def get_document(doc_id: int):
    if not state.index:
        raise HTTPException(status_code=503, detail="Index not loaded")

    if doc_id not in state.index.doc_meta:
        raise HTTPException(status_code=404, detail="Document not found")

    meta = state.index.doc_meta[doc_id]
    text = state.corpus.get(doc_id, "Text not available")

    return {
        "doc_id": doc_id,
        "title": meta.title,
        "length": meta.length,
        "text": text[:2000]
    }


@app.get("/stats", response_model=StatsResponse)
async def get_stats():
    if not state.index:
        raise HTTPException(status_code=503, detail="Index not loaded")

    return StatsResponse(
        num_docs=state.index.num_docs,
        num_terms=len(state.index),
        avg_doc_length=state.index.avg_doc_length
    )


@app.get("/health")
async def health_check():
    if not state.index:
        raise HTTPException(status_code=503, detail="Index not loaded")
    return {"status": "ok"}