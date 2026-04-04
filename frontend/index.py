import html
import time
from pathlib import Path

import streamlit as st


FRONTEND_DIR = Path(__file__).resolve().parent
PAGE_ICON_PATH = FRONTEND_DIR / "assets" / "google-docs.png"


def init_state() -> None:
	if "document_ready" not in st.session_state:
		st.session_state.document_ready = False
	if "processed_file_name" not in st.session_state:
		st.session_state.processed_file_name = ""
	if "chat_history" not in st.session_state:
		st.session_state.chat_history = []


def build_answer(question: str, file_name: str, model_name: str) -> str:
	return (
		f"Tai lieu '{file_name}' da duoc phan tich. "
		f"Cau hoi: '{question}'. "
		f"Cau tra loi demo duoc tao boi {model_name}: "
		"He thong se trich xuat cac doan lien quan tu PDF, tong hop noi dung, "
		"va tra ve cau tra loi gon gang de ban co the tiep tuc hoi them."
	)


st.set_page_config(
	page_title="SmartDocsAI - Document Q&A",
	page_icon=str(PAGE_ICON_PATH) if PAGE_ICON_PATH.exists() else None,
	layout="wide",
	initial_sidebar_state="expanded",
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
}

[data-testid="stAppViewContainer"] {
	background: radial-gradient(circle at 2% 1%, #FFFFFF, var(--bg) 48%);
}

[data-testid="stSidebar"] {
	background-color: var(--sidebar-bg);
	border-right: 1px solid #444B52;
}

[data-testid="stSidebar"] * {
	color: var(--text-sidebar);
}

[data-testid="stSidebar"] .stSlider [data-baseweb="slider"] [role="slider"] {
	background-color: var(--primary);
}

[data-testid="stSidebar"] .stSelectbox div[data-baseweb="select"] > div {
	background-color: #3A3E44;
	border-color: #545B63;
}

[data-testid="stSidebar"] .stSelectbox svg,
[data-testid="stSidebar"] .stSelectbox span {
	color: var(--text-sidebar);
}

.sidebar-card {
	background: linear-gradient(180deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.04));
	border: 1px solid rgba(255, 255, 255, 0.14);
	border-radius: 12px;
	padding: 14px;
	margin-bottom: 14px;
}

.sidebar-card h3 {
	font-family: 'Sora', sans-serif;
	margin: 0 0 10px 0;
	font-size: 1rem;
}

.sidebar-list {
	margin: 0;
	padding-left: 18px;
	line-height: 1.5;
	font-size: 0.93rem;
}

.hero {
	background: linear-gradient(120deg, rgba(0, 123, 255, 0.14), rgba(255, 193, 7, 0.2));
	border: 1px solid var(--muted-border);
	border-radius: 16px;
	padding: 18px 22px;
	margin-bottom: 18px;
}

.hero h1 {
	margin: 0;
	color: var(--text-main);
	font-family: 'Sora', sans-serif;
	font-size: clamp(1.4rem, 2.2vw, 2rem);
}

.hero p {
	margin: 8px 0 0;
	color: #3A4047;
}

.section-title {
	font-family: 'Sora', sans-serif;
	color: var(--text-main);
	font-size: 1.05rem;
	margin-top: 8px;
	margin-bottom: 8px;
}

.status-chip {
	display: inline-block;
	border-radius: 999px;
	padding: 4px 10px;
	font-weight: 600;
	font-size: 0.85rem;
	margin-bottom: 8px;
}

.status-ready {
	color: #0B6E00;
	background: #D9F5D1;
}

.status-waiting {
	color: #8A5A00;
	background: #FFF3CD;
}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] {
	border: 1.5px dashed #B7BEC7;
	background: #FFFFFF;
	border-radius: 14px;
}

[data-testid="stFileUploader"] section[data-testid="stFileUploadDropzone"] button {
	background-color: var(--secondary) !important;
	color: var(--text-main) !important;
	border: 1px solid #E0AE00 !important;
	border-radius: 10px !important;
	font-weight: 700 !important;
}

[data-testid="stButton"] button[kind="primary"] {
	background-color: var(--primary);
	color: #FFFFFF;
	border: 1px solid #0068D6;
	border-radius: 10px;
	font-weight: 700;
}

[data-testid="stButton"] button[kind="secondary"] {
	background-color: var(--secondary);
	color: var(--text-main);
	border: 1px solid #E0AE00;
	border-radius: 10px;
	font-weight: 700;
}

[data-testid="stTextInput"] input {
	border-radius: 10px;
	border: 1px solid #CBD3DB;
}

.qa-card {
	background: var(--surface);
	border: 1px solid var(--muted-border);
	border-left: 5px solid var(--primary);
	border-radius: 12px;
	padding: 12px 14px;
	margin-bottom: 10px;
}

.qa-label {
	font-weight: 700;
	margin-bottom: 3px;
	color: #2E343A;
}

@media (max-width: 900px) {
	.hero {
		padding: 14px 16px;
	}

	.hero p {
		font-size: 0.95rem;
	}
}
</style>
""",
	unsafe_allow_html=True,
)

with st.sidebar:
	st.markdown(
		"""
		<div class="sidebar-card">
			<h3>Instructions</h3>
			<ol class="sidebar-list">
				<li>Upload file PDF</li>
				<li>Process tai lieu de tao index</li>
				<li>Nhap cau hoi ve noi dung</li>
				<li>Xem cau tra loi va tiep tuc hoi</li>
			</ol>
		</div>
		""",
		unsafe_allow_html=True,
	)

	st.markdown('<div class="sidebar-card"><h3>Settings Information</h3></div>', unsafe_allow_html=True)
	temperature = st.slider("Temperature", min_value=0.0, max_value=1.0, value=0.2, step=0.1)
	top_k = st.slider("Top K Retrieval", min_value=1, max_value=20, value=6, step=1)
	max_tokens = st.slider("Max Tokens", min_value=256, max_value=4096, value=1024, step=256)

	st.markdown('<div class="sidebar-card"><h3>Model Configuration</h3></div>', unsafe_allow_html=True)
	model_name = st.selectbox("LLM Model", ["gpt-4o-mini", "gpt-4.1-mini", "claude-3-haiku"])
	embedding_name = st.selectbox(
		"Embedding",
		["text-embedding-3-large", "text-embedding-3-small"],
	)

	st.caption(f"Model: {model_name}")
	st.caption(f"Embedding: {embedding_name}")
	st.caption(f"Temperature: {temperature} | Top K: {top_k} | Max Tokens: {max_tokens}")

	if st.button("Clear Chat", type="secondary"):
		st.session_state.chat_history = []
		st.rerun()

st.markdown(
	"""
	<div class="hero">
		<h1>SmartDocsAI - PDF Question Answering</h1>
		<p>
			Upload tai lieu, xu ly noi dung, sau do dat cau hoi de nhan cau tra loi sinh tu AI.
			Giao dien nay tuan theo palette accessibility va flow su dung tung buoc.
		</p>
	</div>
	""",
	unsafe_allow_html=True,
)

if st.session_state.document_ready:
	st.markdown('<span class="status-chip status-ready">Document ready for Q&A</span>', unsafe_allow_html=True)
else:
	st.markdown('<span class="status-chip status-waiting">Waiting for PDF processing</span>', unsafe_allow_html=True)

st.markdown('<div class="section-title">1) Upload PDF</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
	"Drop your PDF here",
	type=["pdf"],
	help="Chi ho tro dinh dang PDF",
)

if uploaded_file is not None:
	st.info(f"Selected file: {uploaded_file.name}")
	if st.button("Process Document", type="secondary"):
		progress = st.progress(0)
		status = st.empty()
		steps = [
			(15, "Dang tai file len he thong..."),
			(45, "Dang trich xuat text tu PDF..."),
			(75, "Dang tao embedding va index..."),
			(100, "Hoan tat xu ly tai lieu."),
		]

		for percent, message in steps:
			status.write(message)
			progress.progress(percent)
			time.sleep(0.3)

		st.session_state.document_ready = True
		st.session_state.processed_file_name = uploaded_file.name
		st.success("Tai lieu da san sang. Ban co the dat cau hoi ngay bay gio.")

st.markdown('<div class="section-title">2) Query Input</div>', unsafe_allow_html=True)
question = st.text_input(
	"Nhap cau hoi cua ban",
	placeholder="Vi du: Tai lieu nay noi gi ve kien truc he thong?",
)

if st.button("Generate Answer", type="primary"):
	if not st.session_state.document_ready:
		st.warning("Vui long upload va process PDF truoc khi dat cau hoi.")
	elif not question.strip():
		st.warning("Hay nhap cau hoi truoc khi gui.")
	else:
		answer = build_answer(
			question=question.strip(),
			file_name=st.session_state.processed_file_name,
			model_name=model_name,
		)
		st.session_state.chat_history.append(
			{
				"question": question.strip(),
				"answer": answer,
			}
		)

st.markdown('<div class="section-title">3) Answer Display</div>', unsafe_allow_html=True)
if not st.session_state.chat_history:
	st.write("Chua co cau tra loi nao. Hay upload va dat cau hoi de bat dau.")
else:
	for item in reversed(st.session_state.chat_history):
		safe_q = html.escape(item["question"])
		safe_a = html.escape(item["answer"])
		st.markdown(
			f"""
			<div class="qa-card">
				<div class="qa-label">Question</div>
				<div>{safe_q}</div>
				<div class="qa-label" style="margin-top: 8px;">Answer</div>
				<div>{safe_a}</div>
			</div>
			""",
			unsafe_allow_html=True,
		)
