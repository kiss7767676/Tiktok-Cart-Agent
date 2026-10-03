"""Local Ollama research helper."""

from __future__ import annotations

import json
import os
from typing import Any

import httpx

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"
FALLBACK_MODEL_ORDER = (
    "qwen3:4b",
    "qwen3.8:latest",
    "qwen3.8",
    "llama3.2:latest",
    "llama3.2",
    "llama2:latest",
    "llama2",
    "mistral:latest",
    "mistral",
)


def ask_ollama_research(
    query: str,
    model: str | None = None,
    base_url: str | None = None,
    timeout_seconds: float = 240.0,
) -> tuple[str | None, str, str]:
    """Ask a local Ollama model for purchase-focused research guidance."""

    selected_url = (base_url or os.getenv("OSS_MY_OLLAMA_URL") or DEFAULT_OLLAMA_URL).rstrip("/")
    requested_model = (model or os.getenv("OSS_MY_OLLAMA_MODEL") or DEFAULT_OLLAMA_MODEL).strip()
    selected_model = requested_model
    status = "ok"
    prompt = _research_prompt(query)

    try:
        installed_models = _installed_models(selected_url, timeout_seconds=min(timeout_seconds, 10.0))
        if installed_models and requested_model not in installed_models:
            selected_model = _best_installed_model(installed_models)
            status = f"ok_using_installed_model: requested {requested_model} not found"

        answer = _generate_streamed(
            selected_url,
            selected_model,
            prompt,
            timeout_seconds=timeout_seconds,
        )
    except httpx.ConnectError:
        return None, f"ollama_unavailable: start Ollama at {selected_url}", selected_model
    except httpx.HTTPStatusError as error:
        detail = _response_error_detail(error.response)
        if error.response.status_code == 404:
            return None, f"ollama_model_not_found: {selected_model}. {detail}", selected_model
        return None, f"ollama_http_error: {error.response.status_code}. {detail}", selected_model
    except (httpx.TimeoutException, httpx.HTTPError, ValueError) as error:
        return None, f"ollama_error: {error}", selected_model

    if not answer:
        return None, "ollama_empty_response", selected_model

    return answer, status, selected_model


def _generate_streamed(
    base_url: str,
    model: str,
    prompt: str,
    timeout_seconds: float,
) -> str:
    timeout = httpx.Timeout(connect=10.0, read=timeout_seconds, write=10.0, pool=10.0)
    chunks = []
    thinking_chunks = []
    with httpx.stream(
        "POST",
        f"{base_url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": True,
            "think": False,
            "options": {
                "temperature": 0.2,
                "num_predict": 900,
                "stop": ["\n\n However", "\n\n Note: The problem", "\n\n The problem says"],
            },
        },
        timeout=timeout,
    ) as response:
        response.raise_for_status()
        for line in response.iter_lines():
            if not line:
                continue
            payload: dict[str, Any] = json.loads(line)
            chunks.append(str(payload.get("response", "")))
            thinking_chunks.append(str(payload.get("thinking", "")))
            if payload.get("done") is True:
                break
    answer = "".join(chunks).strip()
    if answer:
        return _clean_product_brief(answer)
    return _clean_product_brief("".join(thinking_chunks).strip())


def _installed_models(base_url: str, timeout_seconds: float) -> list[str]:
    response = httpx.get(f"{base_url}/api/tags", timeout=timeout_seconds)
    response.raise_for_status()
    payload: dict[str, Any] = response.json()
    models = payload.get("models", [])
    if not isinstance(models, list):
        return []

    names = []
    for item in models:
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            names.append(item["name"])
    return names


def _best_installed_model(installed_models: list[str]) -> str:
    for model in FALLBACK_MODEL_ORDER:
        if model in installed_models:
            return model
    return installed_models[0]


def _clean_product_brief(answer: str) -> str:
    section_markers = (
        "1. Product description",
        "Product description:",
        "Product Description:",
        "### Product Description",
        "### **Product Description**",
    )
    lowered = answer.lower()
    best_index = -1
    for marker in section_markers:
        index = lowered.rfind(marker.lower())
        best_index = max(best_index, index)
    if best_index > 0:
        return answer[best_index:].strip()
    return answer


def _response_error_detail(response: httpx.Response) -> str:
    try:
        payload = response.json()
    except ValueError:
        return response.text.strip()

    detail = payload.get("error") if isinstance(payload, dict) else None
    return str(detail or payload).strip()


def _research_prompt(query: str) -> str:
    return (
        "/no_think\n"
        "Return only the final product brief. Do not explain your reasoning or planning.\n\n"
        "You are a product research assistant for a Malaysian online shopper. "
        "When given a product name, write a useful product brief. "
        "Do not invent or mention RM amounts, live marketplace facts, current price, stock, vouchers, "
        "seller rating, exact listing specs, or shipping time. If a spec varies by model "
        "or listing, say that it must be confirmed in the Shopee/TikTok listing.\n\n"
        "Format the answer with these sections:\n"
        "1. Product description - 2 short sentences about what the product is and common use cases.\n"
        "2. Typical specifications - 5 to 8 likely specs or attributes shoppers should compare.\n"
        "3. What to check in the listing - 5 exact fields, photos, variations, warranty, and reviews to verify.\n"
        "4. Buying caution - 3 quality risks, compatibility issues, and signs to avoid.\n"
        "5. Recommendation - buy, wait, or compare, with a short reason.\n\n"
        f"Research query: {query}"
    )
