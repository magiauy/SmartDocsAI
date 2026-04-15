from __future__ import annotations

import asyncio
import base64
import json
import time
from pathlib import Path

import httpx
from django.conf import settings


class OCRService:
    def __init__(
        self,
        api_url: str | None = None,
        timeout_seconds: int | None = None,
        api_key: str | None = None,
        api_key_header: str | None = None,
        api_key_prefix: str | None = None,
        request_mode: str | None = None,
        file_field: str | None = None,
        extra_params_json: str | None = None,
        model: str | None = None,
        optional_payload_json: str | None = None,
        poll_seconds: int | None = None,
        job_timeout_seconds: int | None = None,
    ):
        self.api_url = (api_url or getattr(settings, "PADDLEOCR_API_URL", "")).strip()
        self.timeout_seconds = timeout_seconds or int(getattr(settings, "PADDLEOCR_TIMEOUT_SECONDS", 60))
        self.api_key = (api_key or getattr(settings, "PADDLEOCR_API_KEY", "")).strip()
        self.api_key_header = (api_key_header or getattr(settings, "PADDLEOCR_API_KEY_HEADER", "Authorization")).strip()
        self.api_key_prefix = (api_key_prefix or getattr(settings, "PADDLEOCR_API_KEY_PREFIX", "Bearer")).strip()
        self.request_mode = (request_mode or getattr(settings, "PADDLEOCR_REQUEST_MODE", "multipart")).strip().lower()
        self.file_field = (file_field or getattr(settings, "PADDLEOCR_FILE_FIELD", "file")).strip()
        self.extra_params = self._parse_extra_params(extra_params_json or getattr(settings, "PADDLEOCR_EXTRA_PARAMS_JSON", "{}"))
        self.model = (model or getattr(settings, "PADDLEOCR_MODEL", "PaddleOCR-VL-1.5")).strip()
        self.optional_payload = self._parse_extra_params(
            optional_payload_json or getattr(settings, "PADDLEOCR_OPTIONAL_PAYLOAD_JSON", "{}")
        )
        self.poll_seconds = int(poll_seconds or int(getattr(settings, "PADDLEOCR_JOB_POLL_SECONDS", 5)))
        self.job_timeout_seconds = int(job_timeout_seconds or int(getattr(settings, "PADDLEOCR_JOB_TIMEOUT_SECONDS", 300)))

    async def extract_text_from_pdf(self, file_path: Path) -> str:
        if not self.api_url:
            return ""
        if not file_path.exists():
            return ""

        headers = self._build_headers()
        async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
            if self.request_mode == "aistudio-job":
                return await self._extract_text_with_job_api(client=client, file_path=file_path, headers=headers)

            if self.request_mode == "base64-json":
                encoded = base64.b64encode(file_path.read_bytes()).decode("utf-8")
                payload = {self.file_field: encoded, **self.extra_params}
                response = await client.post(self.api_url, json=payload, headers=headers)
            else:
                with file_path.open("rb") as handle:
                    files = {self.file_field: (file_path.name, handle, "application/pdf")}
                    response = await client.post(self.api_url, files=files, data=self.extra_params, headers=headers)

        if response.status_code >= 400:
            raise RuntimeError(f"PaddleOCR request failed ({response.status_code}): {response.text[:200]}")

        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        lines = self._collect_text_lines(payload)
        return "\n".join(line for line in lines if line)

    async def _extract_text_with_job_api(self, client: httpx.AsyncClient, file_path: Path, headers: dict) -> str:
        data = {
            "model": self.model,
        }
        if self.optional_payload:
            data["optionalPayload"] = json.dumps(self.optional_payload)

        with file_path.open("rb") as handle:
            files = {self.file_field: (file_path.name, handle, "application/pdf")}
            response = await client.post(self.api_url, headers=headers, data=data, files=files)

        if response.status_code >= 400:
            raise RuntimeError(f"PaddleOCR job submit failed ({response.status_code}): {response.text[:200]}")

        payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
        job_id = payload.get("data", {}).get("jobId")
        if not job_id:
            raise RuntimeError("PaddleOCR job API did not return jobId")

        result_url = await self._poll_job_result_url(client=client, job_id=str(job_id), headers=headers)
        if not result_url:
            return ""
        return await self._download_job_result_text(client=client, result_url=result_url)

    async def _poll_job_result_url(self, client: httpx.AsyncClient, job_id: str, headers: dict) -> str:
        deadline = time.monotonic() + self.job_timeout_seconds
        status_url = f"{self.api_url.rstrip('/')}/{job_id}"

        while time.monotonic() < deadline:
            response = await client.get(status_url, headers=headers)
            if response.status_code >= 400:
                raise RuntimeError(f"PaddleOCR job poll failed ({response.status_code}): {response.text[:200]}")

            payload = response.json() if response.headers.get("content-type", "").startswith("application/json") else {}
            data = payload.get("data", {})
            state = str(data.get("state", "")).strip().lower()

            if state == "done":
                result_url = data.get("resultUrl", {}).get("jsonUrl")
                if not result_url:
                    raise RuntimeError("PaddleOCR job is done but jsonUrl is missing")
                return result_url

            if state == "failed":
                error_msg = data.get("errorMsg", "Unknown OCR job failure")
                raise RuntimeError(f"PaddleOCR job failed: {error_msg}")

            await asyncio.sleep(max(1, self.poll_seconds))

        raise TimeoutError("PaddleOCR job polling timed out")

    async def _download_job_result_text(self, client: httpx.AsyncClient, result_url: str) -> str:
        response = await client.get(result_url)
        if response.status_code >= 400:
            raise RuntimeError(f"PaddleOCR result download failed ({response.status_code}): {response.text[:200]}")

        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            lines = self._extract_aistudio_markdown_lines(response.json())
            return "\n\n".join(lines)

        lines: list[str] = []
        for raw_line in response.text.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            lines.extend(self._extract_aistudio_markdown_lines(row))

        if lines:
            return "\n\n".join(lines)

        fallback = self._collect_text_lines(response.text)
        return "\n".join(item for item in fallback if item)

    def _extract_aistudio_markdown_lines(self, payload) -> list[str]:
        result = payload.get("result", {}) if isinstance(payload, dict) else {}
        layout_results = result.get("layoutParsingResults", []) if isinstance(result, dict) else []
        lines: list[str] = []
        for block in layout_results:
            markdown_text = block.get("markdown", {}).get("text", "") if isinstance(block, dict) else ""
            if isinstance(markdown_text, str) and markdown_text.strip():
                lines.append(markdown_text.strip())

        if lines:
            return lines
        return self._collect_text_lines(payload)

    def _build_headers(self) -> dict:
        headers = {}
        if not self.api_key:
            return headers

        if self.api_key_prefix:
            headers[self.api_key_header] = f"{self.api_key_prefix} {self.api_key}"
        else:
            headers[self.api_key_header] = self.api_key
        return headers

    def _parse_extra_params(self, raw_value: str) -> dict:
        if not raw_value or not raw_value.strip():
            return {}
        try:
            parsed = json.loads(raw_value)
        except json.JSONDecodeError as exc:
            raise ValueError("PADDLEOCR_EXTRA_PARAMS_JSON must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise ValueError("PADDLEOCR_EXTRA_PARAMS_JSON must be a JSON object")
        return parsed

    def _collect_text_lines(self, payload) -> list[str]:
        if payload is None:
            return []
        if isinstance(payload, str):
            return [payload.strip()] if payload.strip() else []

        if isinstance(payload, dict):
            lines: list[str] = []
            text = payload.get("text")
            if isinstance(text, str) and text.strip():
                lines.append(text.strip())
            for value in payload.values():
                lines.extend(self._collect_text_lines(value))
            return lines

        if isinstance(payload, (list, tuple)):
            # PaddleOCR often returns items like [bbox, [text, confidence]].
            if len(payload) == 2 and isinstance(payload[1], (list, tuple)) and payload[1]:
                maybe_text = payload[1][0]
                if isinstance(maybe_text, str) and maybe_text.strip():
                    return [maybe_text.strip()]
            lines: list[str] = []
            for item in payload:
                lines.extend(self._collect_text_lines(item))
            return lines

        return []
