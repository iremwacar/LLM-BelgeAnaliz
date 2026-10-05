const state = {
  documents: [],
  currentId: localStorage.getItem("belgeanaliz:doc") || null,
  eventSource: null,
  asking: false,
  uploading: false,
};

const els = {
  library: document.getElementById("library"),
  docCount: document.getElementById("docCount"),
  engineStatus: document.getElementById("engineStatus"),
  emptyState: document.getElementById("emptyState"),
  chatLayout: document.getElementById("chatLayout"),
  workspaceTitle: document.getElementById("workspaceTitle"),
  workspaceEyebrow: document.getElementById("workspaceEyebrow"),
  messages: document.getElementById("messages"),
  askForm: document.getElementById("askForm"),
  question: document.getElementById("question"),
  askBtn: document.getElementById("askBtn"),
  steps: document.getElementById("steps"),
  meterFill: document.getElementById("meterFill"),
  progressPercent: document.getElementById("progressPercent"),
  progressDetail: document.getElementById("progressDetail"),
  progressLabel: document.getElementById("progressLabel"),
  previewBtn: document.getElementById("previewBtn"),
  deleteBtn: document.getElementById("deleteBtn"),
  uploadModal: document.getElementById("uploadModal"),
  previewModal: document.getElementById("previewModal"),
  previewFrame: document.getElementById("previewFrame"),
  previewTitle: document.getElementById("previewTitle"),
  uploadError: document.getElementById("uploadError"),
  uploadingMessage: document.getElementById("uploadingMessage"),
};

const stepNames = {
  upload: "Kaydediliyor",
  processing: "İşleniyor",
  images: "Görseller ve metinler analiz ediliyor",
  hierarchy: "Belge bölümleri düzenleniyor",
  embedding: "Arama verileri hazırlanıyor",
  vector_db: "Belge arama sistemine ekleniyor",
  ready: "Belge kullanıma hazır",
};

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatText(value) {
  return escapeHtml(value).replaceAll("\n", "<br>");
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let detail = "İstek tamamlanamadı.";
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch (_) {}
    throw new Error(detail);
  }
  if (response.status === 204) return null;
  return response.json();
}

function setEngineStatus(message, ok = false) {
  els.engineStatus.innerHTML = `<span class="pulse ${ok ? "ok" : ""}"></span>${escapeHtml(message)}`;
}

function readableError(error) {
  const message = error?.message || "Beklenmeyen bir hata oluştu.";
  if (/failed to fetch|networkerror|load failed/i.test(message)) {
    return "Sunucuya bağlanılamadı. Sunucunun çalıştığını kontrol edip yeniden deneyin.";
  }
  return message;
}

async function refreshHealth() {
  try {
    const health = await api("/api/health");
    if (health.models_ready) {
      setEngineStatus("Sistem hazır", true);
    } else if (health.models_loading) {
      setEngineStatus("Modeller hazırlanıyor…");
    } else if (health.error) {
      setEngineStatus(`Sistem hatası: ${health.error}`);
    } else {
      setEngineStatus("Sistem başlatılıyor…");
    }
  } catch (_) {
    setEngineStatus("Sunucuya bağlanılamıyor");
  }
}

async function loadDocuments(selectId = state.currentId) {
  const data = await api("/api/documents");
  state.documents = data.documents || [];
  els.docCount.textContent = String(state.documents.length);
  renderLibrary();

  const chosen = state.documents.find((doc) => doc.id === selectId) || state.documents[0];
  if (chosen) {
    await openDocument(chosen.id);
  } else {
    state.currentId = null;
    localStorage.removeItem("belgeanaliz:doc");
    showEmpty();
  }
}

function documentStatus(status) {
  if (status === "ready") return { className: "ready", label: "Hazır" };
  if (status === "error") return { className: "error", label: "Hata" };
  return { className: "processing", label: "İşleniyor" };
}

function renderLibrary() {
  els.library.innerHTML = state.documents.map((doc) => {
    const status = documentStatus(doc.status);
    const date = doc.created_at ? new Date(doc.created_at).toLocaleString("tr-TR") : "";
    return `
      <button class="doc-item ${doc.id === state.currentId ? "active" : ""}" data-id="${escapeHtml(doc.id)}" type="button">
        <strong>${escapeHtml(doc.name)}</strong>
        <small>${escapeHtml(date)}</small>
        <span class="badge ${status.className}">${status.label}${doc.status !== "ready" && doc.status !== "error" ? ` · ${Number(doc.progress) || 0}%` : ""}</span>
      </button>
    `;
  }).join("");

  els.library.querySelectorAll(".doc-item").forEach((button) => {
    button.addEventListener("click", () => openDocument(button.dataset.id).catch(showPageError));
  });
}

function showPageError(error) {
  setEngineStatus(readableError(error));
}

function showEmpty() {
  els.emptyState.hidden = false;
  els.chatLayout.hidden = true;
  els.previewBtn.hidden = true;
  els.deleteBtn.hidden = true;
  els.workspaceEyebrow.textContent = "Hoş geldiniz";
  els.workspaceTitle.textContent = "Belgelerinizi yükleyin, sorularınıza yanıt alın.";
}

async function openDocument(id) {
  const doc = await api(`/api/documents/${encodeURIComponent(id)}`);
  state.currentId = id;
  localStorage.setItem("belgeanaliz:doc", id);
  els.emptyState.hidden = true;
  els.chatLayout.hidden = false;
  els.previewBtn.hidden = false;
  els.deleteBtn.hidden = false;
  els.workspaceEyebrow.textContent = doc.status === "ready"
    ? "Sorularınızı sorabilirsiniz"
    : doc.status === "error" ? "İşlem tamamlanamadı" : "Belge işleniyor";
  els.workspaceTitle.textContent = doc.name;
  renderLibrary();
  renderMessages(doc.messages || []);
  renderProgress(doc);
  listenForProgress(doc);
  const canAsk = doc.status === "ready";
  els.askBtn.disabled = !canAsk || state.asking;
  els.question.disabled = !canAsk;
}

function renderMessages(messages = []) {
  if (!messages.length) {
    els.messages.innerHTML = `
      <div class="bubble assistant">
        <div class="meta">BelgeAnaliz</div>
        Belgeniz hazır olduğunda içeriği hakkında bir soru sorabilirsiniz.
      </div>
    `;
    return;
  }

  els.messages.innerHTML = messages.map((message) => {
    const sources = Array.isArray(message.sources)
      ? message.sources
      : message.sources?.sources || [];
    const sourceHtml = sources.length
      ? `<div class="sources">${sources.slice(0, 3).map((src) =>
          `Sayfa ${escapeHtml(src.page)} · ${escapeHtml(src.type)}`
        ).join(" · ")}</div>`
      : "";
    const role = message.role === "user" ? "user" : "assistant";
    return `
      <div class="bubble ${role}">
        <div class="meta">${role === "user" ? "Siz" : "BelgeAnaliz"}</div>
        <div>${formatText(message.content)}</div>
        ${sourceHtml}
      </div>
    `;
  }).join("");
  els.messages.scrollTop = els.messages.scrollHeight;
}

function renderProgress(doc) {
  const steps = doc.steps || [];
  const current = doc.current_step || "upload";
  const currentIndex = Math.max(steps.findIndex((step) => step.id === current), 0);
  const percent = Math.max(0, Math.min(100, Number(doc.progress) || 0));

  els.steps.innerHTML = steps.map((step, index) => {
    const done = doc.status === "ready" || index < currentIndex;
    const isCurrent = step.id === current && doc.status !== "ready" && doc.status !== "error";
    const failed = step.id === current && doc.status === "error";
    const label = stepNames[step.id] || step.label || step.id;
    const icon = done ? "✓" : failed ? "!" : String(index + 1);
    return `<li class="${done ? "done" : ""} ${isCurrent ? "current" : ""} ${failed ? "failed" : ""}">
      <span class="step-icon">${icon}</span>
      <span>${escapeHtml(label)}</span>
    </li>`;
  }).join("");

  els.meterFill.style.width = `${doc.status === "ready" ? 100 : percent}%`;
  els.progressPercent.textContent = `${doc.status === "ready" ? 100 : percent}%`;
  const meter = els.meterFill.closest(".meter");
  meter?.setAttribute("aria-valuenow", String(doc.status === "ready" ? 100 : percent));
  els.progressDetail.textContent = doc.error_message || doc.step_detail || "İşlem başlatılıyor…";
  els.progressLabel.textContent =
    doc.status === "ready" ? "Belgeniz hazır" :
    doc.status === "error" ? "İşlem başarısız" : "Belge işleniyor";
}

function listenForProgress(doc) {
  if (state.eventSource) {
    state.eventSource.close();
    state.eventSource = null;
  }
  if (doc.status === "ready" || doc.status === "error") return;

  const docId = doc.id;
  state.eventSource = new EventSource(`/api/documents/${encodeURIComponent(docId)}/events`);
  state.eventSource.onmessage = async (event) => {
    let payload;
    try {
      payload = JSON.parse(event.data);
    } catch (_) {
      return;
    }

    const merged = {
      ...doc,
      current_step: payload.step,
      progress: payload.percent,
      step_detail: payload.detail,
      status: payload.status,
    };

    if (state.currentId === docId) {
      renderProgress(merged);
      els.workspaceEyebrow.textContent =
        payload.status === "ready" ? "Sorularınızı sorabilirsiniz" : "Belge işleniyor";
      els.askBtn.disabled = payload.status !== "ready" || state.asking;
      els.question.disabled = payload.status !== "ready";
    }

    const listed = state.documents.find((item) => item.id === docId);
    if (listed) {
      listed.progress = payload.percent;
      listed.status = payload.status;
      listed.current_step = payload.step;
      renderLibrary();
    }

    if (payload.status === "ready" || payload.status === "error") {
      state.eventSource?.close();
      state.eventSource = null;
      await loadDocuments(docId).catch(showPageError);
    }
  };
  state.eventSource.onerror = () => {
    // EventSource yeniden bağlanmayı kendi yönetir.
  };
}

function showUploadError(message) {
  els.uploadError.textContent = message;
  els.uploadError.hidden = false;
}

function setUploading(uploading) {
  state.uploading = uploading;
  els.uploadingMessage.hidden = !uploading;
  document.querySelectorAll("#modalFileInput, #fileInput").forEach((input) => {
    input.disabled = uploading;
  });
  document.getElementById("cancelUpload").disabled = uploading;
  document.getElementById("closeUpload").disabled = uploading;
}

function validFile(file) {
  const extension = file.name.split(".").pop().toLowerCase();
  const allowed = ["pdf", "png", "jpg", "jpeg", "webp"];
  return allowed.includes(extension);
}

async function uploadFile(file) {
  if (!file || state.uploading) return;
  els.uploadError.hidden = true;

  if (!validFile(file)) {
    showUploadError("Desteklenmeyen dosya biçimi. PDF, PNG, JPG veya WEBP yükleyin.");
    els.uploadModal.hidden = false;
    return;
  }

  setUploading(true);
  els.uploadModal.hidden = false;

  try {
    const body = new FormData();
    body.append("file", file);
    const doc = await api("/api/documents", { method: "POST", body });
    els.uploadModal.hidden = true;
    await loadDocuments(doc.id);
  } catch (error) {
    showUploadError(`Dosya yüklenemedi: ${readableError(error)}`);
  } finally {
    setUploading(false);
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = els.question.value.trim();
  if (!question || !state.currentId || state.asking) return;

  state.asking = true;
  els.askBtn.disabled = true;
  const previousMessages = (await api(`/api/documents/${encodeURIComponent(state.currentId)}`)
    .catch(() => ({ messages: [] }))).messages || [];

  renderMessages([
    ...previousMessages,
    { role: "user", content: question },
    { role: "assistant", content: "Yanıt hazırlanıyor…" },
  ]);
  els.question.value = "";

  try {
    const result = await api(`/api/documents/${encodeURIComponent(state.currentId)}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    renderMessages(result.messages || []);
  } catch (error) {
    renderMessages([
      ...previousMessages,
      { role: "user", content: question },
      { role: "assistant", content: `Yanıt alınamadı: ${readableError(error)}` },
    ]);
  } finally {
    state.asking = false;
    els.askBtn.disabled = !state.currentId ||
      !state.documents.some((doc) => doc.id === state.currentId && doc.status === "ready");
  }
}

function wireDropzone(zone, input) {
  zone.addEventListener("dragover", (event) => {
    event.preventDefault();
    zone.classList.add("drag");
  });
  zone.addEventListener("dragleave", () => zone.classList.remove("drag"));
  zone.addEventListener("drop", async (event) => {
    event.preventDefault();
    zone.classList.remove("drag");
    await uploadFile(event.dataTransfer.files[0]);
  });
  input.addEventListener("change", async () => {
    await uploadFile(input.files[0]);
    input.value = "";
  });
}

document.getElementById("openUpload").addEventListener("click", () => {
  els.uploadError.hidden = true;
  els.uploadModal.hidden = false;
});
document.getElementById("closeUpload").addEventListener("click", () => {
  if (!state.uploading) els.uploadModal.hidden = true;
});
document.getElementById("cancelUpload").addEventListener("click", () => {
  if (!state.uploading) els.uploadModal.hidden = true;
});
document.getElementById("closePreview").addEventListener("click", () => {
  els.previewModal.hidden = true;
  els.previewFrame.src = "";
});
els.previewBtn.addEventListener("click", () => {
  if (!state.currentId) return;
  const doc = state.documents.find((item) => item.id === state.currentId);
  els.previewTitle.textContent = doc?.name || "Belge önizlemesi";
  els.previewFrame.src = `/api/documents/${encodeURIComponent(state.currentId)}/file`;
  els.previewModal.hidden = false;
});
els.deleteBtn.addEventListener("click", async () => {
  if (!state.currentId || !confirm("Bu belgeyi ve kayıtlı sorularını silmek istiyor musunuz?")) return;
  try {
    await api(`/api/documents/${encodeURIComponent(state.currentId)}`, { method: "DELETE" });
    state.currentId = null;
    await loadDocuments();
  } catch (error) {
    showPageError(error);
  }
});
els.askForm.addEventListener("submit", askQuestion);
els.question.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    els.askForm.requestSubmit();
  }
});

wireDropzone(document.getElementById("dropzone"), document.getElementById("fileInput"));
wireDropzone(document.getElementById("modalDropzone"), document.getElementById("modalFileInput"));

refreshHealth();
loadDocuments().catch(showPageError);
setInterval(refreshHealth, 8000);