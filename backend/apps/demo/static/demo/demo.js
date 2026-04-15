const state = {
  documents: [],
  selectedDocumentIds: new Set(),
  conversationId: null,
  conversationStatus: null,
  pollTimer: null,
};

const elements = {
  uploadForm: document.getElementById("upload-form"),
  fileInput: document.getElementById("file-input"),
  refreshDocumentsButton: document.getElementById("refresh-documents-button"),
  documentsList: document.getElementById("documents-list"),
  conversationForm: document.getElementById("conversation-form"),
  conversationTitle: document.getElementById("conversation-title"),
  providerSelect: document.getElementById("provider-select"),
  modelInput: document.getElementById("model-input"),
  conversationStatusCard: document.getElementById("conversation-status-card"),
  chatMessages: document.getElementById("chat-messages"),
  chatForm: document.getElementById("chat-form"),
  chatInput: document.getElementById("chat-input"),
  responseLog: document.getElementById("response-log"),
  connectionPill: document.getElementById("connection-pill"),
};

const providerDefaults = {
  gemini: "gemini-2.5-flash",
  ollama: "qwen2:1.5b",
  mock: "mock-1",
};

function getCookie(name) {
  const cookieValue = document.cookie
    .split(";")
    .map((item) => item.trim())
    .find((item) => item.startsWith(`${name}=`));
  return cookieValue ? decodeURIComponent(cookieValue.split("=")[1]) : "";
}

async function request(url, options = {}) {
  const response = await fetch(url, {
    headers: {
      "X-CSRFToken": getCookie("csrftoken"),
      ...(options.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
    credentials: "same-origin",
    ...options,
  });

  const contentType = response.headers.get("content-type") || "";
  const payload = contentType.includes("application/json")
    ? await response.json()
    : await response.text();

  logPayload(url, response.status, payload);

  if (!response.ok) {
    throw new Error(typeof payload === "string" ? payload : payload.message || "Request failed");
  }

  return payload;
}

function logPayload(url, status, payload) {
  const next = {
    time: new Date().toLocaleTimeString(),
    url,
    status,
    payload,
  };
  elements.responseLog.textContent = JSON.stringify(next, null, 2);
}

function setConnection(text) {
  elements.connectionPill.textContent = text;
}

function badgeClass(value) {
  return `status-badge status-${String(value || "").toLowerCase()}`;
}

function renderDocuments() {
  if (!state.documents.length) {
    elements.documentsList.className = "document-list empty-state";
    elements.documentsList.textContent = "No documents loaded yet.";
    return;
  }

  elements.documentsList.className = "document-list";
  elements.documentsList.innerHTML = state.documents
    .map((document) => {
      const checked = state.selectedDocumentIds.has(document.id) ? "checked" : "";
      return `
        <article class="document-card">
          <label>
            <input type="checkbox" data-document-id="${document.id}" ${checked}>
            <div>
              <header>
                <span class="document-title">${document.title}</span>
                <span class="${badgeClass(document.processing_status)}">${document.processing_status}</span>
              </header>
              <div class="document-meta">summary: ${document.summary_status} | source: ${document.source}</div>
            </div>
          </label>
        </article>
      `;
    })
    .join("");

  elements.documentsList.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
    checkbox.addEventListener("change", (event) => {
      const documentId = Number(event.target.dataset.documentId);
      if (event.target.checked) {
        state.selectedDocumentIds.add(documentId);
      } else {
        state.selectedDocumentIds.delete(documentId);
      }
    });
  });
}

function renderConversationStatus() {
  if (!state.conversationId) {
    elements.conversationStatusCard.innerHTML = "<strong>No active conversation.</strong><p>Create one after choosing documents.</p>";
    return;
  }

  elements.conversationStatusCard.innerHTML = `
    <header>
      <strong>Conversation #${state.conversationId}</strong>
      <span class="${badgeClass(state.conversationStatus)}">${state.conversationStatus}</span>
    </header>
    <p>${state.conversationStatus === "ready" ? "Conversation is ready for chat." : "Waiting for summaries and indexing to finish."}</p>
  `;
}

function renderMessages(messages) {
  if (!messages.length) {
    elements.chatMessages.className = "chat-messages empty-state";
    elements.chatMessages.textContent = "No messages yet.";
    return;
  }

  elements.chatMessages.className = "chat-messages";
  elements.chatMessages.innerHTML = messages
    .map((message) => `
      <article class="message-card ${message.role}">
        <header>
          <span class="message-role">${message.role}</span>
          <span class="message-meta">${message.model || ""}</span>
        </header>
        <div>${escapeHtml(message.content)}</div>
      </article>
    `)
    .join("");
}

function appendMessage(role, content, model = "") {
  const current = Array.from(elements.chatMessages.querySelectorAll(".message-card")).map((card) => ({
    role: card.dataset.role,
    content: card.querySelector("div")?.textContent || "",
    model: card.querySelector(".message-meta")?.textContent || "",
  }));
  current.push({ role, content, model });
  renderMessages(current);
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

async function loadDocuments() {
  setConnection("Loading documents");
  const payload = await request("/api/documents/");
  state.documents = payload.data.documents || [];
  renderDocuments();
  setConnection("Documents loaded");
}

async function loadMessages() {
  if (!state.conversationId) return;
  const payload = await request(`/api/conversations/${state.conversationId}/messages/`);
  renderMessages(payload.data.messages || []);
}

async function pollConversationStatus() {
  if (!state.conversationId) return;
  const payload = await request(`/api/conversations/${state.conversationId}/status/`);
  state.conversationStatus = payload.data.status;
  renderConversationStatus();

  if (state.conversationStatus === "ready") {
    window.clearInterval(state.pollTimer);
    state.pollTimer = null;
    setConnection("Conversation ready");
    await loadMessages();
  }
}

elements.uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const files = Array.from(elements.fileInput.files || []);
  if (!files.length) {
    setConnection("Select files first");
    return;
  }

  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));

  setConnection("Uploading");
  const payload = await request("/api/documents/upload/", {
    method: "POST",
    body: formData,
  });

  const newDocuments = payload.data.documents || [];
  state.documents = [...newDocuments, ...state.documents.filter((item) => !newDocuments.some((next) => next.id === item.id))];
  renderDocuments();
  elements.uploadForm.reset();
  setConnection("Upload complete");
});

elements.refreshDocumentsButton.addEventListener("click", async () => {
  await loadDocuments();
});

elements.providerSelect.addEventListener("change", () => {
  const defaultModel = providerDefaults[elements.providerSelect.value];
  elements.modelInput.value = defaultModel;
});

elements.conversationForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.selectedDocumentIds.size) {
    setConnection("Pick at least one document");
    return;
  }

  setConnection("Creating conversation");
  const payload = await request("/api/conversations/", {
    method: "POST",
    body: JSON.stringify({
      title: elements.conversationTitle.value.trim() || "Demo Conversation",
      provider: elements.providerSelect.value,
      model: elements.modelInput.value.trim() || "mock-1",
      document_ids: Array.from(state.selectedDocumentIds),
    }),
  });

  state.conversationId = payload.data.id;
  state.conversationStatus = payload.data.status;
  renderConversationStatus();
  await loadMessages();

  if (state.pollTimer) {
    window.clearInterval(state.pollTimer);
  }
  if (state.conversationStatus !== "ready") {
    state.pollTimer = window.setInterval(pollConversationStatus, 2500);
  }
  setConnection(`Conversation ${state.conversationStatus}`);
});

elements.chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!state.conversationId) {
    setConnection("Create a conversation first");
    return;
  }

  const content = elements.chatInput.value.trim();
  if (!content) {
    setConnection("Enter a question");
    return;
  }

  setConnection("Sending message");
  try {
    const payload = await request(`/api/conversations/${state.conversationId}/messages/`, {
      method: "POST",
      body: JSON.stringify({ role: "user", content }),
    });
    await loadMessages();
    elements.chatInput.value = "";
    setConnection("Message sent");
    return payload;
  } catch (error) {
    setConnection(error.message);
  }
});

window.addEventListener("load", async () => {
  try {
    await loadDocuments();
  } catch (error) {
    setConnection(error.message);
  }
});
