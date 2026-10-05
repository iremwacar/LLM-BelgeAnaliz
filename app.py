from contextlib import asynccontextmanager
import asyncio
import json
import shutil
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from core.library_store import LibraryStore
from core.runtime import get_runtime, op_lock, warmup_async

ROOT = Path(__file__).resolve().parent
UPLOAD_DIR = ROOT / "storage" / "uploads"
FRONTEND_DIR = ROOT / "frontend"
ALLOWED_EXTENSIONS = {".pdf", ".png", ".jpg", ".jpeg", ".webp"}

PIPELINE_STEPS = [
    {"id": "upload", "label": "Kaydediliyor"},
    {"id": "processing", "label": "İşleniyor"},
    {"id": "images", "label": "Görseller analiz ediliyor"},
    {"id": "hierarchy", "label": "Bilgi hiyerarşisi oluşturuluyor"},
    {"id": "embedding", "label": "Gömme oluşturuluyor"},
    {"id": "vector_db", "label": "Vektör veri tabanına aktarılıyor"},
    {"id": "ready", "label": "Sorular için hazır"},
]

store = LibraryStore()
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    warmup_async()
    yield


app = FastAPI(title="BelgeAnaliz", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class QuestionBody(BaseModel):
    question: str


def serialize_document(doc: dict, include_messages: bool = False) -> dict:
    payload = {
        "id": doc["id"],
        "name": doc["original_name"],
        "status": doc["status"],
        "progress": doc["progress"],
        "current_step": doc["current_step"],
        "step_detail": doc["step_detail"],
        "chunk_count": doc["chunk_count"],
        "error_message": doc["error_message"],
        "created_at": doc["created_at"],
        "updated_at": doc["updated_at"],
        "steps": PIPELINE_STEPS,
    }
    if include_messages:
        payload["messages"] = store.list_messages(doc["id"])
    return payload


def push_progress(doc_id: str, step: str, percent: int, detail: str, status: Optional[str] = None):
    store.update_document(
        doc_id,
        current_step=step,
        progress=percent,
        step_detail=detail,
        status=status or "processing",
    )
    event = {
        "document_id": doc_id,
        "step": step,
        "percent": percent,
        "detail": detail,
        "status": status or "processing",
    }
    with jobs_lock:
        job = jobs.setdefault(doc_id, {"events": [], "done": False})
        job["events"].append(event)
        if status in {"ready", "error"}:
            job["done"] = True


def ingest_worker(doc_id: str, file_path: str):
    try:
        push_progress(doc_id, "processing", 2, "Loading embedding engines")
        runtime = get_runtime()
        pipeline = runtime["pipeline"]
        push_progress(doc_id, "processing", 6, "Engines ready — processing document")

        def progress_cb(step, percent, detail=""):
            push_progress(doc_id, step, percent, detail)

        with op_lock:
            result = pipeline.ingest_document(file_path, document_id=doc_id, progress_cb=progress_cb)
        store.update_document(doc_id, chunk_count=result.get("chunk_count", 0))
        push_progress(doc_id, "ready", 100, "Document is ready for questions", status="ready")
    except Exception as exc:
        push_progress(doc_id, "error", 100, str(exc), status="error")
        store.update_document(doc_id, error_message=str(exc))


@app.get("/api/health")
def health():
    from core.runtime import _runtime

    return {
        "ok": True,
        "models_ready": bool(_runtime["ready"]),
        "models_loading": bool(_runtime["loading"]),
        "error": _runtime["error"],
        "steps": PIPELINE_STEPS,
    }


@app.get("/api/documents")
def list_documents():
    return {"documents": [serialize_document(doc) for doc in store.list_documents()]}


@app.get("/api/documents/{doc_id}")
def get_document(doc_id: str):
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return serialize_document(doc, include_messages=True)


@app.get("/api/documents/{doc_id}/file")
def get_document_file(doc_id: str):
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    path = Path(doc["file_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="Original file is missing")
    return FileResponse(
        path,
        filename=doc["original_name"],
        content_disposition_type="inline",
    )


@app.post("/api/documents")
async def upload_document(file: UploadFile = File(...)):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Supported files: PDF, PNG, JPG, WEBP")

    doc_id = str(uuid.uuid4())
    dest_dir = UPLOAD_DIR / doc_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / (file.filename or f"document{suffix}")
    with dest_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    store.create_document(doc_id, file.filename or dest_path.name, str(dest_path))
    push_progress(doc_id, "upload", 4, "Saving document")
    threading.Thread(target=ingest_worker, args=(doc_id, str(dest_path)), daemon=True).start()
    doc = store.get_document(doc_id)
    return serialize_document(doc)


@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    try:
        runtime = get_runtime()
        runtime["pipeline"].delete_document_vectors(doc_id)
    except Exception:
        pass
    file_dir = Path(doc["file_path"]).parent
    shutil.rmtree(file_dir, ignore_errors=True)
    store.delete_document(doc_id)
    with jobs_lock:
        jobs.pop(doc_id, None)
    return {"ok": True}


@app.get("/api/documents/{doc_id}/events")
async def document_events(doc_id: str):
    if not store.get_document(doc_id):
        raise HTTPException(status_code=404, detail="Document not found")

    async def event_stream():
        cursor = 0
        while True:
            with jobs_lock:
                job = jobs.get(doc_id, {"events": [], "done": False})
                events = job["events"][cursor:]
                done = job["done"]
            for event in events:
                cursor += 1
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
            if done:
                break
            doc = store.get_document(doc_id)
            with jobs_lock:
                remaining = len(jobs.get(doc_id, {}).get("events", []))
            if doc and doc["status"] in {"ready", "error"} and cursor >= remaining:
                yield f"data: {json.dumps({'document_id': doc_id, 'step': doc['current_step'], 'percent': doc['progress'], 'detail': doc['step_detail'], 'status': doc['status']}, ensure_ascii=False)}\n\n"
                break
            await asyncio.sleep(0.35)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/api/documents/{doc_id}/ask")
def ask_question(doc_id: str, body: QuestionBody):
    question = (body.question or "").strip()
    if not question:
        raise HTTPException(status_code=400, detail="Please enter a question")

    doc = store.get_document(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    if doc["status"] != "ready":
        raise HTTPException(status_code=409, detail="Document is still being processed")

    runtime = get_runtime()
    with op_lock:
        answer, image_refs, contexts = runtime["rag"].generate_answer(question, document_id=doc_id)
    sources = [
        {
            "page": ctx.get("page"),
            "type": ctx.get("type"),
            "score": ctx.get("score"),
            "content": (ctx.get("content") or "")[:400],
            "image_path": ctx.get("image_path"),
        }
        for ctx in contexts
    ]
    store.add_message(str(uuid.uuid4()), doc_id, "user", question)
    store.add_message(
        str(uuid.uuid4()),
        doc_id,
        "assistant",
        answer,
        sources={"sources": sources, "image_refs": list(set(image_refs or []))},
    )
    return {
        "answer": answer,
        "sources": sources,
        "image_refs": list(set(image_refs or [])),
        "messages": store.list_messages(doc_id),
    }


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
