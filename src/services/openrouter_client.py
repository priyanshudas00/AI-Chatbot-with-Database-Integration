from typing import Any, Dict, List, Optional

from openai import OpenAI
from openai import APIStatusError
from openai import RateLimitError as OpenAIRateLimitError

from src.config import Settings
from src.exceptions import ApiError, RateLimitError


class OpenRouterClient:
    def __init__(self, settings: Settings) -> None:
        self.api_key = settings.openrouter_api_key
        self.base_url = settings.openrouter_base_url
        self.chat_model = settings.openrouter_chat_model
        self.embedding_model = settings.openrouter_embedding_model
        self.client = OpenAI(base_url=self.base_url, api_key=self.api_key)

    def generate_reply(
        self,
        user_message: str,
        history: Optional[List[Dict[str, str]]] = None,
    ) -> tuple[str, int | None]:
        if not self.api_key:
            raise ApiError("Missing OPENROUTER_API_KEY in environment.")
        if not user_message.strip() and not history:
            raise ApiError("Chat input is required.")

        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": "You are a helpful AI assistant. Answer clearly and concisely.",
            }
        ]
        if history:
            for item in history:
                role = item.get("role", "user")
                content = item.get("content", "")
                if role in ("user", "assistant") and content:
                    messages.append({"role": role, "content": content})
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.chat_model,
                messages=messages,
                max_tokens=512,
            )
        except OpenAIRateLimitError as error:
            raise RateLimitError(f"OpenRouter chat rate-limited: {error}") from error
        except APIStatusError as error:
            if error.status_code == 429:
                raise RateLimitError(f"OpenRouter chat rate-limited: {error}") from error
            raise ApiError(f"OpenRouter chat request failed: {error}") from error
        except Exception as error:
            raise ApiError(f"OpenRouter chat request failed: {error}") from error

        raw = response.model_dump()
        choices = raw.get("choices") or []
        if not choices:
            raise ApiError("OpenRouter chat response had no choices.")
        reply = (choices[0].get("message") or {}).get("content") or ""
        if not reply.strip():
            raise ApiError("OpenRouter chat response had empty content.")

        usage = raw.get("usage") or {}
        token_count = usage.get("total_tokens")
        if token_count is None:
            token_count = usage.get("completion_tokens")

        return reply, token_count

    def generate_embedding(self, text: str) -> Dict[str, Any]:
        if not self.api_key:
            raise ApiError("Missing OPENROUTER_API_KEY in environment.")
        if not text.strip():
            raise ApiError("Embedding input text is required.")

        try:
            response = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
                encoding_format="float",
            )
        except OpenAIRateLimitError as error:
            raise RateLimitError(f"OpenRouter embeddings rate-limited: {error}") from error
        except APIStatusError as error:
            if error.status_code == 429:
                raise RateLimitError(f"OpenRouter embeddings rate-limited: {error}") from error
            raise ApiError(f"OpenRouter embeddings request failed: {error}") from error
        except Exception as error:
            raise ApiError(f"OpenRouter embeddings request failed: {error}") from error

        raw = response.model_dump()
        if not raw.get("data"):
            raise ApiError("OpenRouter embeddings response had no vector data.")
        return raw
