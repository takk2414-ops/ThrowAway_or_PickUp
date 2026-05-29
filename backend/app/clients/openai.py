"""OpenAI API から論文分析を生成する client です。"""

from functools import lru_cache
import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.analyses import PaperAIAnalysisCreate
from app.schemas.papers import PaperResponse


OPENAI_API_BASE_URL = "https://api.openai.com/v1/"


class OpenAIConfigError(RuntimeError):
    """OpenAI API設定が不足している場合のエラーです。"""


class OpenAIClientError(RuntimeError):
    """OpenAI APIへの問い合わせやレスポンス解析に失敗した場合のエラーです。"""


@lru_cache
def get_openai_client() -> httpx.Client:
    settings = get_settings()
    if not settings.openai_api_key:
        raise OpenAIConfigError("OPENAI_API_KEY is not configured")

    return httpx.Client(
        base_url=OPENAI_API_BASE_URL,
        headers={
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )


def _analysis_json_schema() -> dict[str, Any]:
    difficulty_schema = {
        "type": "integer",
        "description": "1から5までの整数。1が易しく、5が非常に難しい。",
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "summary_ja": {
                "type": "string",
                "description": "Abstractの内容を日本語で2〜4文に要約する。",
            },
            "implementation_difficulty": difficulty_schema,
            "implementation_reason": {
                "type": "string",
                "description": "実装難易度の理由を日本語で簡潔に説明する。",
            },
            "reading_difficulty": difficulty_schema,
            "reading_reason": {
                "type": "string",
                "description": "文章難易度の理由を日本語で簡潔に説明する。",
            },
            "math_difficulty": difficulty_schema,
            "math_reason": {
                "type": "string",
                "description": "数学的難易度の理由を日本語で簡潔に説明する。",
            },
        },
        "required": [
            "summary_ja",
            "implementation_difficulty",
            "implementation_reason",
            "reading_difficulty",
            "reading_reason",
            "math_difficulty",
            "math_reason",
        ],
    }


def _build_analysis_prompt(paper: PaperResponse) -> str:
    abstract = paper.abstract or "Abstract is not available."
    authors = ", ".join(paper.authors) if paper.authors else "Unknown"
    return (
        "以下の論文Abstractを分析してください。\n"
        "難易度は1〜5で、1が易しい、5が非常に難しいという意味です。\n"
        "Abstractだけでは判断しきれない場合は、推測であることが分かる理由にしてください。\n\n"
        f"Title: {paper.title}\n"
        f"Authors: {authors}\n"
        f"Abstract:\n{abstract}"
    )


def _extract_output_text(response_data: dict[str, Any]) -> str:
    output_text = response_data.get("output_text")
    if isinstance(output_text, str):
        return output_text

    output = response_data.get("output")
    if not isinstance(output, list):
        raise OpenAIClientError("OpenAI returned unexpected response shape")

    text_parts: list[str] = []
    for item in output:
        if not isinstance(item, dict):
            continue
        content = item.get("content")
        if not isinstance(content, list):
            continue
        for content_item in content:
            if not isinstance(content_item, dict):
                continue
            text = content_item.get("text")
            if isinstance(text, str):
                text_parts.append(text)

    if not text_parts:
        raise OpenAIClientError("OpenAI response did not contain output text")
    return "".join(text_parts)


def analyze_paper_abstract(
    paper: PaperResponse,
    model: str,
) -> PaperAIAnalysisCreate:
    payload = {
        "model": model,
        "input": [
            {
                "role": "system",
                "content": (
                    "You analyze computer science papers for Japanese backend "
                    "engineers. Return only the requested JSON structure."
                ),
            },
            {
                "role": "user",
                "content": _build_analysis_prompt(paper),
            },
        ],
        "text": {
            "format": {
                "type": "json_schema",
                "name": "paper_ai_analysis",
                "strict": True,
                "schema": _analysis_json_schema(),
            }
        },
    }

    try:
        response = get_openai_client().post("responses", json=payload)
        response.raise_for_status()
    except OpenAIConfigError:
        raise
    except httpx.HTTPError as error:
        raise OpenAIClientError("OpenAI analysis request failed") from error

    try:
        response_data = response.json()
        parsed_output = json.loads(_extract_output_text(response_data))
    except (ValueError, TypeError) as error:
        raise OpenAIClientError("OpenAI returned invalid analysis JSON") from error

    try:
        return PaperAIAnalysisCreate.model_validate(
            {
                "paper_id": paper.id,
                "provider": "openai",
                "model": model,
                **parsed_output,
                "raw_response": response_data,
            }
        )
    except ValidationError as error:
        raise OpenAIClientError("OpenAI analysis JSON failed validation") from error
