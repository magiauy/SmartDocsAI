from asgiref.sync import async_to_sync
from django.conf import settings

from apps.llm.interfaces.base import CompletionRequest
from apps.llm.services.provider_factory import ProviderFactory


DEFAULT_SYSTEM_PROMPT = (
    "Bạn là một trợ lý ảo thông minh chuyên phân tích tài liệu. "
    "Hãy trả lời CHỈ dựa vào ngữ cảnh được cung cấp. "
    "Nếu không có đáp án trong tài liệu, hãy trả lời đúng câu: 'Tài liệu không đề cập đến'."
)

MAX_CONTEXT_HITS = 4
MAX_CONTEXT_CHARS_PER_HIT = 450


class CompletionService:
    def __init__(self, factory=None):
        self.factory = factory or ProviderFactory(settings)

    def generate(
        self,
        provider: str,
        model: str,
        prompt: str,
        context_hits: list[dict] | None = None,
        chat_history: list[dict] | None = None,
        system_prompt: str = "",
    ):
        hits = context_hits or []
        history = chat_history or []
        compiled_prompt = self._build_prompt(
            provider=provider,
            model=model,
            user_prompt=prompt,
            context_hits=hits,
            chat_history=history,
            system_prompt=system_prompt,
        )
        request = CompletionRequest(provider=provider, model=model, prompt=compiled_prompt, context_hits=hits)
        client = self.factory.build(provider)
        response = async_to_sync(client.generate)(request)
        return {
            "provider": response.provider,
            "model": response.model,
            "content": response.content,
            "tokens_input": response.tokens_input,
            "tokens_output": response.tokens_output,
            "latency_ms": response.latency_ms,
        }

    def _build_prompt(
        self,
        provider: str,
        model: str,
        user_prompt: str,
        context_hits: list[dict],
        chat_history: list[dict],
        system_prompt: str,
    ) -> str:
        context_blocks = []
        for index, hit in enumerate(context_hits[:MAX_CONTEXT_HITS], start=1):
            metadata = hit.get("metadata", {})
            source = metadata.get("file_id") or metadata.get("document_id") or "unknown"
            content = hit.get("content", "").strip()
            if len(content) > MAX_CONTEXT_CHARS_PER_HIT:
                content = content[:MAX_CONTEXT_CHARS_PER_HIT].rstrip() + "..."
            context_blocks.append(f"[{index}] (source={source}) {content}")

        if not context_blocks:
            context_blocks.append("(Không có ngữ cảnh truy xuất)")

        history_blocks = []
        for item in chat_history:
            role = item.get("role", "user")
            content = item.get("content", "").strip()
            if content:
                history_blocks.append(f"{role}: {content}")

        if not history_blocks:
            history_blocks.append("(Không có lịch sử hội thoại)")

        prompt_parts = [
            f"[SYSTEM]\n{system_prompt or DEFAULT_SYSTEM_PROMPT}",
            f"[MODEL_PROFILE]\nprovider={provider}; model={model}",
            "[CONTEXT]\n" + "\n".join(context_blocks),
            "[CHAT_HISTORY]\n" + "\n".join(history_blocks),
            f"[QUESTION]\n{user_prompt.strip()}",
            (
                "[INSTRUCTION]\n"
                "1) Chỉ được dùng thông tin trong CONTEXT.\n"
                "2) Nếu không đủ thông tin, trả lời đúng: 'Tài liệu không đề cập đến'.\n"
                "3) Nếu có thông tin, trả lời ngắn gọn 1-4 câu và thêm trích dẫn nguồn dạng [n] ở cuối câu liên quan.\n"
                "4) Không bịa thêm dữ kiện ngoài CONTEXT."
            ),
        ]
        return "\n\n".join(prompt_parts)
