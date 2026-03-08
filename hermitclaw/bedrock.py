"""AWS Bedrock provider support."""

import json
import logging
import os
from typing import Any

logger = logging.getLogger("hermitclaw.bedrock")

# Lazy-loaded boto3 client
_bedrock_client = None


def _get_bedrock_client():
    """Get or create Bedrock runtime client."""
    global _bedrock_client
    if _bedrock_client is None:
        try:
            import boto3
            region = os.environ.get("AWS_REGION", "us-east-1")
            _bedrock_client = boto3.client("bedrock-runtime", region_name=region)
        except ImportError:
            raise ImportError(
                "boto3 is required for Bedrock. Install with: pip install hermitclaw[bedrock]"
            )
    return _bedrock_client


def _build_claude_request(messages: list[dict], max_tokens: int) -> dict:
    """Build request body for Claude models."""
    # Convert messages to Claude format
    claude_messages = []
    system = None
    
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        
        if role == "system":
            system = content
        elif role in ("user", "assistant"):
            # Handle multimodal content
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict):
                        if part.get("type") == "text":
                            parts.append({"type": "text", "text": part.get("text", "")})
                        elif part.get("type") == "image_url":
                            # Convert base64 image to Claude format
                            image_url = part.get("image_url", "")
                            if image_url.startswith("data:"):
                                # Parse data URL
                                import base64
                                mime_end = image_url.index(";")
                                data_start = image_url.index(",") + 1
                                mime_type = image_url[5:mime_end]
                                image_data = image_url[data_start:]
                                parts.append({
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": mime_type,
                                        "data": image_data,
                                    }
                                })
                claude_messages.append({"role": role, "content": parts})
            else:
                claude_messages.append({"role": role, "content": [{"type": "text", "text": str(content)}]})
        elif role == "tool":
            # Tool results in Claude format
            tool_call_id = msg.get("tool_call_id", "")
            tool_content = msg.get("content", "")
            claude_messages.append({
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": tool_call_id,
                    "content": tool_content,
                }]
            })
    
    request = {
        "max_tokens": max_tokens,
        "messages": claude_messages,
    }
    if system:
        request["system"] = system
    
    return request


def _build_llama_request(messages: list[dict], max_tokens: int) -> dict:
    """Build request body for Llama models."""
    # Convert to simple format
    formatted = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            # Extract text from multimodal
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = " ".join(text_parts)
        formatted.append({"role": role, "content": str(content)})
    
    return {
        "max_gen_len": max_tokens,
        "messages": formatted,
    }


def _build_mistral_request(messages: list[dict], max_tokens: int) -> dict:
    """Build request body for Mistral models."""
    formatted = []
    for msg in messages:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        if isinstance(content, list):
            text_parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text_parts.append(part.get("text", ""))
            content = " ".join(text_parts)
        formatted.append({"role": role, "content": str(content)})
    
    return {
        "max_tokens": max_tokens,
        "messages": formatted,
    }


def _get_model_provider(model_id: str) -> str:
    """Determine the provider from model ID."""
    model_lower = model_id.lower()
    if "claude" in model_lower:
        return "anthropic"
    elif "llama" in model_lower:
        return "meta"
    elif "mistral" in model_lower:
        return "mistral"
    elif "titan" in model_lower:
        return "amazon"
    else:
        # Default to anthropic format
        return "anthropic"


def _parse_claude_response(response: dict) -> dict:
    """Parse Claude response into standard format."""
    output = response.get("output", {})
    message = output.get("message", {})
    content_blocks = message.get("content", [])
    
    text = ""
    tool_calls = []
    
    for block in content_blocks:
        if block.get("type") == "text":
            text += block.get("text", "")
        elif block.get("type") == "tool_use":
            tool_calls.append({
                "id": block.get("id", ""),
                "type": "function",
                "function": {
                    "name": block.get("name", ""),
                    "arguments": json.dumps(block.get("input", {})),
                }
            })
    
    return {
        "text": text or None,
        "tool_calls": [
            {
                "name": tc["function"]["name"],
                "arguments": json.loads(tc["function"]["arguments"]),
                "call_id": tc["id"],
            }
            for tc in tool_calls
        ],
        "output": [
            {"type": "message", "content": [{"type": "text", "text": text}]} if text else None,
            *[{"type": "function_call", **tc} for tc in tool_calls]
        ] if text or tool_calls else [],
    }


def _parse_llama_response(response: dict) -> dict:
    """Parse Llama response into standard format."""
    generation = response.get("generation", "")
    return {
        "text": generation or None,
        "tool_calls": [],
        "output": [{"type": "message", "content": [{"type": "text", "text": generation}]}] if generation else [],
    }


def _parse_mistral_response(response: dict) -> dict:
    """Parse Mistral response into standard format."""
    outputs = response.get("outputs", [])
    text = ""
    if outputs:
        text = outputs[0].get("text", "")
    return {
        "text": text or None,
        "tool_calls": [],
        "output": [{"type": "message", "content": [{"type": "text", "text": text}]}] if text else [],
    }


def bedrock_chat(
    messages: list[dict],
    model: str,
    max_tokens: int = 1000,
    tools: list[dict] | None = None,
) -> dict:
    """Make a Bedrock chat completion call.
    
    Args:
        messages: List of message dicts with role and content
        model: Bedrock model ID (e.g., anthropic.claude-3-sonnet-20240229-v1:0)
        max_tokens: Maximum tokens to generate
        tools: Optional list of tool definitions (Claude only for now)
    
    Returns:
        Dict with text, tool_calls, and output fields
    """
    client = _get_bedrock_client()
    provider = _get_model_provider(model)
    
    # Build request based on provider
    if provider == "anthropic":
        body = _build_claude_request(messages, max_tokens)
        if tools:
            # Convert tools to Claude format
            claude_tools = []
            for tool in tools:
                if tool.get("type") == "function":
                    func = tool.get("function", {})
                    claude_tools.append({
                        "name": func.get("name", ""),
                        "description": func.get("description", ""),
                        "input_schema": func.get("parameters", {}),
                    })
            body["tools"] = claude_tools
    elif provider == "meta":
        body = _build_llama_request(messages, max_tokens)
    elif provider == "mistral":
        body = _build_mistral_request(messages, max_tokens)
    else:
        # Fallback to Claude format
        body = _build_claude_request(messages, max_tokens)
    
    # Make the API call
    response = client.invoke_model(
        modelId=model,
        body=json.dumps(body),
    )
    response_body = json.loads(response["body"].read())
    
    # Parse response based on provider
    if provider == "anthropic":
        return _parse_claude_response(response_body)
    elif provider == "meta":
        return _parse_llama_response(response_body)
    elif provider == "mistral":
        return _parse_mistral_response(response_body)
    else:
        return _parse_claude_response(response_body)


def bedrock_embed(text: str, model: str = "amazon.titan-embed-text-v2:0") -> list[float]:
    """Get embeddings from Bedrock.
    
    Args:
        text: Text to embed
        model: Bedrock embedding model ID
    
    Returns:
        List of floats representing the embedding
    """
    client = _get_bedrock_client()
    
    response = client.invoke_model(
        modelId=model,
        body=json.dumps({"inputText": text}),
    )
    response_body = json.loads(response["body"].read())
    
    return response_body.get("embedding", [])
