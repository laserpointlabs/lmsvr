"""
External API clients for OpenAI and Claude pass-through.
"""
import httpx
import os
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


async def openai_chat_completions(
    model: str,
    messages: list,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    top_p: Optional[float] = None,
    tools: Optional[list] = None,
    stream: Optional[bool] = False
) -> Dict[str, Any]:
    """Send chat completion request to OpenAI API."""
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not configured")

    payload = {
        "model": model,
        "messages": messages
    }

    if temperature is not None:
        payload["temperature"] = temperature
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if top_p is not None:
        payload["top_p"] = top_p
    if tools is not None:
        payload["tools"] = tools
    if stream is not None:
        payload["stream"] = stream

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        return response.json()


def calculate_openai_cost(model: str, usage: Dict[str, Any]) -> float:
    """
    Calculate cost for OpenAI API usage.
    Based on OpenAI pricing (approximate, update as needed).
    """
    # Pricing per 1M tokens (as of 2024, update as needed)
    pricing = {
        "gpt-4": {"input": 30.0, "output": 60.0},
        "gpt-4-turbo": {"input": 10.0, "output": 30.0},
        "gpt-4o": {"input": 5.0, "output": 15.0},
        "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    }

    model_pricing = pricing.get(model, {"input": 0.5, "output": 1.5})

    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost


async def claude_messages(
    model: str,
    messages: list,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None
) -> Dict[str, Any]:
    """Send messages request to Claude API."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY not configured")

    payload = {
        "model": model,
        "messages": messages
    }

    if max_tokens is not None:
        payload["max_tokens"] = max_tokens
    if temperature is not None:
        payload["temperature"] = temperature

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json"
            },
            json=payload
        )
        response.raise_for_status()
        return response.json()


def calculate_claude_cost(model: str, usage: Dict[str, Any]) -> float:
    """
    Calculate cost for Claude API usage.
    Based on Anthropic pricing (approximate, update as needed).
    """
    # Pricing per 1M tokens (as of 2024, update as needed)
    pricing = {
        "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
        "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
        "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    }

    model_pricing = pricing.get(model, {"input": 0.25, "output": 1.25})

    input_tokens = usage.get("input_tokens", 0)
    output_tokens = usage.get("output_tokens", 0)

    input_cost = (input_tokens / 1_000_000) * model_pricing["input"]
    output_cost = (output_tokens / 1_000_000) * model_pricing["output"]

    return input_cost + output_cost
