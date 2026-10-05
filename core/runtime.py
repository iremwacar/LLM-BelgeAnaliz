import threading
from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

from core.ingestion_pipeline import TusasIngestionPipeline
from core.rag_engine import TusasRAGEngine

COLLECTION_NAME = "tusas_doc_collection"
DB_PATH = "./qdrant_data"

_lock = threading.Lock()
_runtime = {
    "ready": False,
    "loading": False,
    "error": None,
    "pipeline": None,
    "rag": None,
}
op_lock = threading.Lock()


def get_runtime(block=True):
    with _lock:
        if _runtime["ready"]:
            return _runtime
        if _runtime["error"] and not _runtime["loading"]:
            _runtime["error"] = None
        if not _runtime["loading"]:
            _runtime["loading"] = True
        else:
            if not block:
                return _runtime

        try:
            model = SentenceTransformer("BAAI/bge-m3", model_kwargs={"use_safetensors": True})
            client = QdrantClient(path=DB_PATH)
            pipeline = TusasIngestionPipeline(
                collection_name=COLLECTION_NAME,
                client=client,
                model=model,
                recreate_collection=False,
            )
            rag = TusasRAGEngine(
                collection_name=COLLECTION_NAME,
                client=client,
                model=model,
            )
            _runtime.update(
                ready=True,
                loading=False,
                error=None,
                pipeline=pipeline,
                rag=rag,
            )
        except Exception as exc:
            _runtime.update(ready=False, loading=False, error=str(exc))
            raise
        return _runtime


def warmup_async():
    thread = threading.Thread(target=_safe_warmup, daemon=True)
    thread.start()


def _safe_warmup():
    try:
        get_runtime()
    except Exception:
        pass
