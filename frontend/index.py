import html
import os
import time
from pathlib import Path

import httpx
import streamlit as st


FRONTEND_DIR = Path(__file__).resolve().parent
PAGE_ICON_PATH = FRONTEND_DIR / "assets" / "google-docs.png"
API_BASE_URL = os.getenv("SMARTDOCSAI_API_BASE_URL", "http://localhost:8000").rstrip("/")
POLL_INTERVAL_SECONDS = float(os.getenv("SMARTDOCSAI_FE_POLL_INTERVAL_SECONDS", "2"))
DOCUMENT_POLL_TIMEOUT_SECONDS = int(os.getenv("SMARTDOCSAI_FE_DOCUMENT_TIMEOUT_SECONDS", "180"))
CONVERSATION_POLL_TIMEOUT_SECONDS = int(os.getenv("SMARTDOCSAI_FE_CONVERSATION_TIMEOUT_SECONDS", "120"))
LLM_PROVIDER = os.getenv("SMARTDOCSAI_LLM_PROVIDER", "gemini").strip().lower()
LLM_MODEL = os.getenv(
	"SMARTDOCSAI_LLM_MODEL",
	os.getenv("GEMINI_MODEL", "gemini-2.5-flash") if LLM_PROVIDER == "gemini" else os.getenv("OLLAMA_MODEL", "qwen2:1.5b"),
).strip()


def _split_csv_env(value: str) -> list[str]:
	return [item.strip() for item in value.split(",") if item.strip()]


def build_model_options() -> list[tuple[str, str]]:
	gemini_default = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
	ollama_default = os.getenv("OLLAMA_MODEL", "qwen2:1.5b").strip()

	gemini_models = _split_csv_env(os.getenv("SMARTDOCSAI_GEMINI_MODELS", "gemini-2.5-flash,gemini-2.5-pro"))
	ollama_models = _split_csv_env(os.getenv("SMARTDOCSAI_OLLAMA_MODELS", ollama_default))

	if gemini_default and gemini_default not in gemini_models:
		gemini_models.insert(0, gemini_default)
	if ollama_default and ollama_default not in ollama_models:
		ollama_models.insert(0, ollama_default)

	options: list[tuple[str, str]] = []
	for model in gemini_models:
		options.append(("gemini", model))
	for model in ollama_models:
		options.append(("ollama", model))

	# Keep order stable and avoid duplicate provider/model pairs.
	seen: set[tuple[str, str]] = set()
	unique_options: list[tuple[str, str]] = []
	for option in options:
		if option in seen:
			continue
		seen.add(option)
		unique_options.append(option)

	if not unique_options:
		unique_options = [(LLM_PROVIDER, LLM_MODEL)]

	return unique_options


MODEL_OPTIONS = build_model_options()


def init_state() -> None:
	if "document_ready" not in st.session_state:
		st.session_state.document_ready = False
	if "processed_file_name" not in st.session_state:
		st.session_state.processed_file_name = ""
	if "chat_history" not in st.session_state:
		st.session_state.chat_history = []
	if "uploaded_files" not in st.session_state:
		st.session_state.uploaded_files = []
	if "active_document_id" not in st.session_state:
		st.session_state.active_document_id = None
	if "conversation_id" not in st.session_state:
		st.session_state.conversation_id = None
	if "conversation_ready" not in st.session_state:
		st.session_state.conversation_ready = False
	if "last_error" not in st.session_state:
		st.session_state.last_error = ""
	if "last_hits" not in st.session_state:
		st.session_state.last_hits = []


def register_uploaded_file(file_name: str, document_id: int | None = None) -> None:
	if not file_name:
		return

	for item in st.session_state.uploaded_files:
		if item["name"] == file_name:
			if document_id is not None:
				item["document_id"] = document_id
			return

	st.session_state.uploaded_files.append({"name": file_name, "processed": False, "document_id": document_id})


def mark_uploaded_file_processed(file_name: str) -> None:
	for item in st.session_state.uploaded_files:
		if item["name"] == file_name:
			item["processed"] = True
			return


def api_request(method: str, path: str, *, json_payload=None, files=None, timeout=60.0, allow_status_codes=None):
	allow_status_codes = set(allow_status_codes or [])
	url = f"{API_BASE_URL}{path}"
	with httpx.Client(timeout=timeout) as client:
		response = client.request(method, url, json=json_payload, files=files)
	try:
		payload = response.json()
	except ValueError:
		raise RuntimeError(f"Backend returned invalid JSON (HTTP {response.status_code}).")

	if response.status_code >= 400 and response.status_code not in allow_status_codes:
		data_message = payload.get("data", {}).get("message") if isinstance(payload.get("data"), dict) else None
		error_message = data_message or payload.get("message") or payload.get("errors") or response.text
		raise RuntimeError(str(error_message))

	if not payload.get("success", False):
		raise RuntimeError(payload.get("message", "Backend request failed."))
	return payload.get("data", {})


def poll_document_ready(document_id: int, *, timeout_seconds: int = DOCUMENT_POLL_TIMEOUT_SECONDS, on_update=None):
	deadline = time.time() + timeout_seconds
	while time.time() < deadline:
		data = api_request("GET", f"/api/documents/{document_id}/status/")
		if on_update:
			on_update(data)
		if data.get("processing_status") == "indexed":
			return data
		if data.get("processing_status") == "failed":
			raise RuntimeError(data.get("error_message") or "Document indexing failed.")
		time.sleep(POLL_INTERVAL_SECONDS)
	raise TimeoutError("Document indexing did not finish in time.")


def ensure_conversation(model_name: str, provider: str, on_update=None):
	if st.session_state.conversation_id and st.session_state.conversation_ready:
		return st.session_state.conversation_id

	if st.session_state.active_document_id is None:
		raise RuntimeError("No processed document found.")

	if not st.session_state.conversation_id:
		created = api_request(
			"POST",
			"/api/conversations/",
			json_payload={
				"title": f"Chat about {st.session_state.processed_file_name}",
				"provider": provider,
				"model": model_name,
				"document_ids": [st.session_state.active_document_id],
			},
		)
		st.session_state.conversation_id = created.get("id")

	deadline = time.time() + CONVERSATION_POLL_TIMEOUT_SECONDS
	while time.time() < deadline:
		status_data = api_request("GET", f"/api/conversations/{st.session_state.conversation_id}/status/")
		if on_update:
			on_update(status_data)
		if status_data.get("status") == "ready":
			st.session_state.conversation_ready = True
			return st.session_state.conversation_id
		if status_data.get("status") == "failed":
			raise RuntimeError("Conversation preparation failed.")
		time.sleep(POLL_INTERVAL_SECONDS)

	raise TimeoutError("Conversation is still preparing.")


def refresh_chat_history(conversation_id: int):
	data = api_request("GET", f"/api/conversations/{conversation_id}/messages/")
	messages = data.get("messages", [])
	st.session_state.chat_history = [
		{"role": message.get("role", "assistant"), "content": message.get("content", "")}
		for message in messages
	]


def render_sidebar_sources() -> None:
	"""Render uploaded files list in sidebar."""
	if not st.session_state.uploaded_files:
		st.markdown('<div class="source-empty">No uploaded files yet.</div>', unsafe_allow_html=True)
		return

	for item in st.session_state.uploaded_files:
		safe_name = html.escape(item["name"])
		state = "ready" if item["processed"] else "uploaded"
		pill_class = "source-pill-ready" if item["processed"] else "source-pill-uploaded"
		st.markdown(
			f'<div class="source-item"><div class="source-name" title="{safe_name}">{safe_name}</div>'
			f'<div class="source-pill {pill_class}">{state}</div></div>',
			unsafe_allow_html=True,
		)


def build_chat_html() -> str:
	"""Build complete chat stream HTML with all messages properly nested."""
	if not st.session_state.chat_history:
		return '<div class="chat-stream"><div class="chat-empty">Upload and process a PDF to begin chatting.</div></div>'

	messages = []
	for item in st.session_state.chat_history:
		role = item.get("role", "assistant")
		content = html.escape(item.get("content", ""))
		if role == "user":
			messages.append(f'<div class="chat-row user"><div class="chat-bubble user">{content}</div></div>')
		else:
			messages.append(f'<div class="chat-row assistant"><div class="chat-bubble assistant">{content}</div></div>')

	return '<div class="chat-stream">' + "".join(messages) + "</div>"


st.set_page_config(
	page_title="SmartDocsAI - Document Q&A",
	page_icon=str(PAGE_ICON_PATH) if PAGE_ICON_PATH.exists() else None,
	layout="wide",
)

init_state()

st.markdown(
	"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&display=swap');

:root {
	--primary: #007BFF;
	--secondary: #FFC107;
	--bg: #F8F9FA;
	--sidebar-bg: #2C2F33;
	--text-main: #212529;
	--text-sidebar: #FFFFFF;
	--surface: #FFFFFF;
	--muted-border: #DDE2E7;
}

html, body, [class*="css"] {
	font-family: 'IBM Plex Sans', sans-serif;
	height: 100%;
	overflow: hidden;
}

[data-testid="stAppViewContainer"] {
	background: radial-gradient(circle at 2% 1%, #FFFFFF, var(--bg) 48%);
}

.block-container {
	height: calc(100vh - 1rem);
	overflow: hidden;
	padding-top: 0.75rem;
	padding-bottom: 0.75rem;
	display: flex;
	flex-direction: column;
}

[data-testid="stSidebar"] {
	background-color: var(--sidebar-bg);
	border-right: 1px solid #444B52;
}

[data-testid="stSidebar"] * {
	color: var(--text-sidebar);
}

[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
	background-color: #3A3E44;
	border-color: #545B63;
}

[data-testid="stSidebar"] .stSelectbox svg,
[data-testid="stSidebar"] .stSelectbox span {
	color: var(--text-sidebar);
}

.sidebar-shell {
	font-family: 'Sora', sans-serif;
	font-size: 0.86rem;
	font-weight: 600;
	letter-spacing: 0.04em;
	text-transform: uppercase;
	margin: 0 0 10px 0;
	opacity: 0.9;
}

.sidebar-block {
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
	border: 1px solid rgba(255, 255, 255, 0.14);
	border-radius: 12px;
	padding: 12px;
	margin-bottom: 10px;
}

.source-item {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
	padding: 8px 10px;
	border-radius: 9px;
	background: rgba(255, 255, 255, 0.09);
	margin-bottom: 8px;
}

.source-item:last-child {
	margin-bottom: 0;
}

.source-name {
	font-size: 0.85rem;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
	max-width: 160px;
}

.source-pill {
	font-size: 0.68rem;
	font-weight: 700;
	padding: 2px 8px;
	border-radius: 999px;
	text-transform: uppercase;
	letter-spacing: 0.02em;
}

.source-pill-ready {
	background: #D9F5D1;
	color: #0B6E00 !important;
}

.source-pill-uploaded {
	background: #FFF3CD;
	color: #8A5A00 !important;
}

.source-empty {
	font-size: 0.85rem;
	opacity: 0.82;
	padding: 6px 2px;
}

[data-testid="stFileUploader"] {
	background: transparent !important;
}

[data-testid="stFileUploader"] section {
	background: transparent !important;
}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {
	border: 2px dashed var(--secondary) !important;
	background: rgba(255, 255, 255, 0.08) !important;
	border-radius: 12px !important;
	padding: 20px !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] section {
	border: 2px dashed var(--secondary) !important;
}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] span,
[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] div {
	color: var(--text-sidebar) !important;
}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] button {
	background-color: var(--secondary) !important;
	color: var(--text-main) !important;
	border: 1px solid #E0AE00 !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
}

[data-testid="stSidebar"] [data-testid="stFileUploader"] button {
	background-color: var(--secondary) !important;
	color: var(--text-main) !important;
	border: 1px solid #E0AE00 !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
}

[data-testid="stButton"] button[kind="primary"] {
	background-color: var(--primary) !important;
	color: #FFFFFF !important;
	border: 1px solid #0068D6 !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
}

[data-testid="stButton"] button[kind="secondary"] {
	background-color: var(--secondary) !important;
	color: var(--text-main) !important;
	border: 1px solid #E0AE00 !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
}

[data-testid="stTextInput"] input {
	border-radius: 10px !important;
	border: 1px solid #CBD3DB !important;
	background-color: #FFFFFF !important;
	color: var(--text-main) !important;
}

.st-dd {
	background-color: #FFFFFF !important;
}

[data-testid="stForm"] {
	background: linear-gradient(to bottom, rgba(248, 249, 250, 0), var(--bg)) !important;
	border: none !important;
	padding: 12px 0 !important;
	position: sticky !important;
	bottom: 0;
	z-index: 100;
	margin-top: 10px !important;
	padding-top: 8px !important;
	padding-bottom: 8px !important;
	padding-left: 1rem !important;
	padding-right: 1rem !important;
}

.main-chat-title {
	font-family: 'Sora', sans-serif;
	font-size: 1.35rem;
	font-weight: 700;
	color: var(--text-main);
	text-align: center;
	padding-top: 20px;
	margin-bottom: 12px;
	margin-top: 20px;
}

.chat-stream {
	height: calc(100vh - 20rem);
	min-height: 250px;
	max-height: calc(100vh - 20rem);
	background: var(--surface);
	border: 1px solid var(--muted-border);
	border-radius: 16px;
	padding: 16px;
	overflow-y: auto;
	overflow-x: hidden;
	display: flex;
	flex-direction: column;
	gap: 10px;
	scroll-behavior: smooth;
}

.chat-stream::-webkit-scrollbar {
	width: 8px;
}

.chat-stream::-webkit-scrollbar-track {
	background: transparent;
}

.chat-stream::-webkit-scrollbar-thumb {
	background: #CBD3DB;
	border-radius: 4px;
}

.chat-stream::-webkit-scrollbar-thumb:hover {
	background: #B7BEC7;
}

.chat-row {
	display: flex;
	margin: 0;
}

.chat-row.user {
	justify-content: flex-end;
}

.chat-row.assistant {
	justify-content: flex-start;
}

.chat-bubble {
	max-width: 74%;
	padding: 10px 14px;
	border-radius: 14px;
	line-height: 1.5;
	font-size: 0.95rem;
	word-wrap: break-word;
}

.chat-bubble.user {
	background: var(--primary);
	color: #FFFFFF;
	border-radius: 14px 4px 14px 14px;
}

.chat-bubble.assistant {
	background: #F0F2F5;
	color: var(--text-main);
	border: 1px solid var(--muted-border);
	border-radius: 4px 14px 14px 14px;
}

.chat-empty {
	display: flex;
	align-items: center;
	justify-content: center;
	height: 100%;
	color: #66707A;
	font-size: 0.95rem;
}

.send-error {
	margin-top: 2px;
	font-size: 0.9rem;
	font-weight: 600;
	color: #D92D20;
}

@media (max-width: 900px) {
	html, body, [class*="css"] {
		overflow: auto;
	}

	.block-container {
		height: auto;
		overflow: visible;
	}

	.chat-stream {
		height: calc(100vh - 24rem);
		max-height: calc(100vh - 24rem);
		min-height: 180px;
	}
}
</style>
""",
	unsafe_allow_html=True,
)

with st.sidebar:
	st.markdown('<div class="sidebar-shell">SmartDocsAI</div>', unsafe_allow_html=True)
	st.caption(f"API: {API_BASE_URL}")

	uploaded_file = st.file_uploader(
		"Upload PDF",
		type=["pdf"],
		label_visibility="collapsed",
		help="Upload PDF document",
	)

	if uploaded_file is not None:
		st.caption(f"Selected: {uploaded_file.name}")
		if st.button("Process", type="secondary", use_container_width=True):
			progress = st.progress(0)
			status = st.empty()
			try:
				st.session_state.last_error = ""
				st.session_state.last_hits = []
				status.write("Uploading file...")
				file_payload = [("files", (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type or "application/pdf"))]
				response = api_request("POST", "/api/documents/upload/", files=file_payload)
				documents = response.get("documents", [])
				if not documents:
					raise RuntimeError("Upload succeeded but no document metadata was returned.")
				document = documents[0]
				st.session_state.active_document_id = document.get("id")
				st.session_state.conversation_id = None
				st.session_state.conversation_ready = False
				st.session_state.document_ready = False
				st.session_state.processed_file_name = uploaded_file.name
				register_uploaded_file(uploaded_file.name, document_id=document.get("id"))
				progress.progress(35)

				status.write("Building index...")
				poll_document_ready(
					document.get("id"),
					on_update=lambda payload: status.write(
						f"Building index... ({payload.get('processing_status', 'processing')})"
					),
				)
				progress.progress(100)

				st.session_state.document_ready = True
				mark_uploaded_file_processed(uploaded_file.name)
				st.success("Ready to chat")
			except Exception as exc:
				st.session_state.last_error = str(exc)
				st.error(f"Processing failed: {exc}")

	render_sidebar_sources()
	st.markdown('</div></div>', unsafe_allow_html=True)

	default_option = next((opt for opt in MODEL_OPTIONS if opt == (LLM_PROVIDER, LLM_MODEL)), MODEL_OPTIONS[0])
	default_index = MODEL_OPTIONS.index(default_option)

	st.markdown('<div class="sidebar-block"><strong>Model</strong></div>', unsafe_allow_html=True)
	selected_option = st.selectbox(
		"LLM Model",
		MODEL_OPTIONS,
		index=default_index,
		format_func=lambda opt: f"{opt[1]} ({opt[0]})",
		label_visibility="collapsed",
	)
	selected_provider, model_name = selected_option

	if st.session_state.last_hits:
		with st.expander(f"Retrieval hits ({len(st.session_state.last_hits)})", expanded=False):
			for idx, hit in enumerate(st.session_state.last_hits, start=1):
				metadata = hit.get("metadata") or {}
				score = hit.get("score", 0)
				document_id = metadata.get("document_id", "n/a")
				chunk_index = metadata.get("chunk_index", "n/a")
				content = str(hit.get("content", "")).strip()[:220]
				st.markdown(f"**Hit {idx}** - score: `{score:.4f}` - doc: `{document_id}` - chunk: `{chunk_index}`")
				st.caption(content or "(empty chunk)")

	if st.button("Clear Chat", type="secondary", use_container_width=True):
		st.session_state.chat_history = []
		st.session_state.last_hits = []
		st.session_state.last_error = ""
		st.session_state.conversation_id = None
		st.session_state.conversation_ready = False
		st.rerun()

st.markdown('<div class="main-chat-title">SmartDocsAI Chat</div>', unsafe_allow_html=True)

if st.session_state.last_error:
	st.error(f"Last error: {st.session_state.last_error}")

# Render complete chat stream with all messages properly nested
st.markdown(build_chat_html(), unsafe_allow_html=True)

with st.form("chat_form", clear_on_submit=True):
	input_col, send_col = st.columns([1, 0.14], gap="small")
	with input_col:
		question = st.text_input(
			"Message",
			placeholder="Ask about your PDF...",
			label_visibility="collapsed",
		)
	with send_col:
		submitted = st.form_submit_button("Send", type="primary", use_container_width=True)

if submitted:
	if not st.session_state.document_ready:
		st.markdown('<div class="send-error">Upload and process a PDF first.</div>', unsafe_allow_html=True)
	elif not question.strip():
		st.error("Enter a question.")
	else:
		try:
			conversation_status = st.empty()
			conversation_id = ensure_conversation(
				model_name,
				selected_provider,
				on_update=lambda payload: conversation_status.info(
					f"Conversation status: {payload.get('status', 'preparing')}"
				),
			)
			result = api_request(
				"POST",
				f"/api/conversations/{conversation_id}/messages/",
				json_payload={"role": "user", "content": question.strip()},
				allow_status_codes={409},
			)
			if result.get("ready_for_chat") is False:
				st.warning("Conversation is still preparing. Please wait a few seconds and send again.")
				st.session_state.last_hits = []
				st.stop()
			st.session_state.last_hits = result.get("hits", [])
			refresh_chat_history(conversation_id)
			st.rerun()
		except Exception as exc:
			st.session_state.last_error = str(exc)
			st.error(f"Send failed: {exc}")
			if selected_provider == "ollama" and "unavailable" in str(exc).lower():
				st.info("Ollama is not reachable from backend. Start it with: docker-compose -f backend/docker-compose.yml --profile ollama up -d ollama")
