import html
import time
from pathlib import Path

import streamlit as st

FRONTEND_DIR = Path(__file__).resolve().parent
PAGE_ICON_PATH = FRONTEND_DIR / "assets" / "google-docs.png"
UI_DIR = FRONTEND_DIR / "ui"
CSS_PATH = UI_DIR / "styles.css"
TEMPLATES_DIR = UI_DIR / "templates"


def init_state() -> None:
    if "document_ready" not in st.session_state:
        st.session_state.document_ready = False
    if "processed_file_name" not in st.session_state:
        st.session_state.processed_file_name = ""
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "sources" not in st.session_state:
        st.session_state.sources = []


def build_answer(question: str, file_name: str, model_name: str) -> str:
    return (
        f"Dựa trên tài liệu '{file_name}', đây là thông tin cho câu hỏi: '{question}'.\n\n"
        f"Phản hồi này được tạo bởi **{model_name}**. "
        "Hệ thống đã trích xuất các phần liên quan từ tài liệu, "
        "tổng hợp nội dung để cung cấp một câu trả lời chính xác và ngắn gọn "
        "trực tiếp vào trọng tâm vấn đề bạn đang nghiên cứu."
    )


def load_template(name: str, **kwargs: str) -> str:
    content = (TEMPLATES_DIR / name).read_text(encoding="utf-8")
    return content.format(**kwargs) if kwargs else content


def inject_styles() -> None:
    css = CSS_PATH.read_text(encoding="utf-8")
    st.markdown(f"<style>\n{css}\n</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="NotebookLM AI",
    page_icon=str(PAGE_ICON_PATH) if PAGE_ICON_PATH.exists() else None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

init_state()
inject_styles()


def render_left_panel(empty_mode: bool = False) -> str:
    model_name = st.session_state.get("left_panel_model_select", "gemini-1.5-pro")
    with st.container():
        st.markdown('<div id="lp_root_marker"></div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div id="lp_title">NotebookLM</div>
            <div id="lp_subtitle">Sources</div>
            """,
            unsafe_allow_html=True,
        )

        # Sources box (uploader + list)
        with st.container():
            st.markdown('<div id="lp_sources_area_marker"></div>', unsafe_allow_html=True)
            uploaded_file = st.file_uploader(
                "Add source",
                type=["pdf", "txt", "md", "docx"],
                label_visibility="collapsed",
                key="left_panel_uploader",
            )
            st.markdown('<div id="lp_upload_helper">', unsafe_allow_html=True)
            st.markdown(load_template("upload_helper.html"), unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    if uploaded_file is not None and uploaded_file.name not in [s["name"] for s in st.session_state.sources]:
        with st.spinner("Processing document..."):
            time.sleep(1.2)
            st.session_state.sources.append({
                "name": uploaded_file.name,
                "type": uploaded_file.type,
            })
            st.session_state.document_ready = True
            st.session_state.processed_file_name = uploaded_file.name
            st.rerun()

        st.markdown('<div id="lp_sources_list_marker"></div>', unsafe_allow_html=True)
        if not st.session_state.sources:
            st.markdown(load_template("no_sources.html"), unsafe_allow_html=True)
        else:
            for source in st.session_state.sources:
                escaped_name = html.escape(source["name"])
                st.markdown(load_template("source_card.html", source_name=escaped_name), unsafe_allow_html=True)

        # Model + actions
        st.markdown('<div id="lp_model_area_marker"></div>', unsafe_allow_html=True)
        st.markdown(load_template("model_label.html"), unsafe_allow_html=True)

        model_name = st.selectbox(
            "LLM Model",
            ["gemini-1.5-pro", "gemini-1.5-flash", "gpt-4o", "claude-3.5-sonnet"],
            label_visibility="collapsed",
            key="left_panel_model_select",
        )

        if st.button("Clear chat", use_container_width=True, key="left_panel_clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # Apply empty-mode spacing on the styled container (CSS targets this class)
    if empty_mode:
        st.markdown(
            "<script>document.currentScript?.closest('[data-testid=\"stVerticalBlock\"]').classList.add('empty-mode');</script>",
            unsafe_allow_html=True,
        )

    return model_name


if not st.session_state.document_ready:
    left, main = st.columns([1.05, 3.2], gap="large")

    with left:
        render_left_panel(empty_mode=True)

    with main:
        st.markdown(load_template("empty_topbar.html"), unsafe_allow_html=True)
        st.markdown(load_template("empty_state.html"), unsafe_allow_html=True)

else:
    left, center, right = st.columns([1.05, 2.2, 1.1], gap="large")

    with left:
        model_name = render_left_panel()

    with center:
        st.markdown(
            load_template(
                "document_topbar.html",
                processed_file_name=html.escape(st.session_state.processed_file_name),
            ),
            unsafe_allow_html=True,
        )

        if not st.session_state.chat_history:
            st.markdown(
                load_template(
                    "guide_card.html",
                    processed_file_name=html.escape(st.session_state.processed_file_name),
                ),
                unsafe_allow_html=True,
            )

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if prompt := st.chat_input("Ask about your sources..."):
            st.session_state.chat_history.append({"role": "user", "content": prompt})

            with st.chat_message("user"):
                st.markdown(prompt)

            with st.chat_message("assistant"):
                message_placeholder = st.empty()
                full_response = ""
                answer = build_answer(prompt, st.session_state.processed_file_name, model_name)

                for chunk in answer.split():
                    full_response += chunk + " "
                    time.sleep(0.03)
                    message_placeholder.markdown(full_response + "▌")

                message_placeholder.markdown(full_response)

            st.session_state.chat_history.append({"role": "assistant", "content": full_response})

    with right:
        st.markdown(load_template("studio_card.html"), unsafe_allow_html=True)