import os
import json
import logging
from typing import List, Dict, Any
import anthropic

logger = logging.getLogger(__name__)


class ClaudeClientError(Exception):
    """Base exception for SecurityAssistant-specific errors"""

    pass


class ClaudeClient:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 4096

    def prompt_chain(self, model, data, message: str, chain: str):
        """Execute a prompt chain with Claude"""
        current_model = model if model is not None else self.model
        messages = []

        logger.debug("")
        for item in data:
            messages.append(
                {"role": "user", "content": f"{json.dumps(item, indent=2)}"}
            )

        messages.append({"role": "user", "content": message})

        try:
            response = self.client.messages.create(
                model=current_model,
                max_tokens=self.max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": chain,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=messages,
            )

            logger.debug(f"Usage: {response.usage}")
            logger.debug(f"Content: {response.content[0]}")

            if isinstance(response.content, list) and hasattr(
                response.content[0], "text"
            ):
                json_str = response.content[0].text
                results = json.loads(json_str)
                logger.debug("Parsed JSON response:\n%s", json.dumps(results, indent=2))
                return results
            else:
                raise ClaudeClientError("Unexpected response format")

        except (json.JSONDecodeError, AttributeError) as e:
            logger.error("Failed to parse response: %s", e)
            raise ClaudeClientError(f"Failed to parse response: {str(e)}")
