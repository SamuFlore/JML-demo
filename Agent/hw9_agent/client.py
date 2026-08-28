from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class ModelClientError(RuntimeError):
    pass


def extract_output_text(payload: dict[str, Any]) -> str:
    direct = payload.get("output_text")
    if isinstance(direct, str) and direct:
        return direct
    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") == "output_text" and isinstance(content.get("text"), str):
                chunks.append(content["text"])
    if not chunks:
        raise ModelClientError("Responses API result contained no output_text content")
    return "\n".join(chunks)


def extract_chat_content(payload: dict[str, Any]) -> str:
    try:
        content = payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise ModelClientError("Chat Completions result contained no assistant message") from exc
    if not isinstance(content, str) or not content:
        raise ModelClientError("Chat Completions assistant message was empty")
    return content


@dataclass
class OpenAIResponsesClient:
    model: str
    api_key: str | None = None
    base_url: str = "https://api.openai.com/v1"
    timeout: int = 180

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ModelClientError(
                "OPENAI_API_KEY is not set. Configure it in the environment; do not store it in this repository."
            )
        if not self.model:
            raise ModelClientError("A model must be supplied with --model or OPENAI_MODEL")

    def generate(self, prompt: str) -> str:
        body = json.dumps({"model": self.model, "input": prompt}).encode("utf-8")
        request = Request(
            self.base_url.rstrip("/") + "/responses",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ModelClientError(f"Responses API HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ModelClientError(f"Responses API request failed: {exc}") from exc
        return extract_output_text(payload)


@dataclass
class DeepSeekChatClient:
    model: str = "deepseek-chat"
    api_key: str | None = None
    base_url: str = "https://api.deepseek.com"
    timeout: int = 180

    def __post_init__(self) -> None:
        self.api_key = self.api_key or os.environ.get("DEEPSEEK_API_KEY")
        if not self.api_key:
            raise ModelClientError(
                "DEEPSEEK_API_KEY is not set. Configure it in the environment; do not store it in this repository."
            )
        if not self.model:
            raise ModelClientError("A DeepSeek model name is required")

    def generate(self, prompt: str) -> str:
        body = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }).encode("utf-8")
        request = Request(
            self.base_url.rstrip("/") + "/chat/completions",
            data=body,
            method="POST",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        try:
            with urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise ModelClientError(f"DeepSeek API HTTP {exc.code}: {detail}") from exc
        except (URLError, TimeoutError) as exc:
            raise ModelClientError(f"DeepSeek API request failed: {exc}") from exc
        return extract_chat_content(payload)
