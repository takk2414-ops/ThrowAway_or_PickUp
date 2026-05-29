"""Gemini API から論文分析を生成する client です。"""

from functools import lru_cache
import json
from typing import Any

import httpx
from pydantic import ValidationError

from app.config import get_settings
from app.schemas.analyses import PaperAIAnalysisCreate
from app.schemas.papers import PaperResponse


GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/"


class GeminiConfigError(RuntimeError):
    """Gemini API設定が不足している場合のエラーです。"""


class GeminiClientError(RuntimeError):
    """Gemini APIへの問い合わせやレスポンス解析に失敗した場合のエラーです。"""


@lru_cache
def get_gemini_client() -> httpx.Client:
    settings = get_settings()
    if not settings.gemini_api_key:
        raise GeminiConfigError("GEMINI_API_KEY is not configured")

    return httpx.Client(
        base_url=GEMINI_API_BASE_URL,
        headers={"Content-Type": "application/json"},
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
                "description": (
                    "Abstractの内容を、情報系の大学生が理解できる平易な日本語で"
                    "2〜4文に要約する。"
                ),
            },
            "implementation_difficulty": difficulty_schema,
            "implementation_reason": {
                "type": "string",
                "description": (
                    "実装難易度の理由を、専門用語を補いながら平易な日本語で"
                    "簡潔に説明する。"
                ),
            },
            "reading_difficulty": difficulty_schema,
            "reading_reason": {
                "type": "string",
                "description": (
                    "文章難易度の理由を、情報系の学生目線で平易な日本語で"
                    "簡潔に説明する。"
                ),
            },
            "math_difficulty": difficulty_schema,
            "math_reason": {
                "type": "string",
                "description": (
                    "数学的難易度の理由を、必要な数学知識が分かるように"
                    "平易な日本語で簡潔に説明する。"
                ),
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
        "読者は情報系の大学生です。研究経験が浅くても理解できるように、"
        "難しい専門用語はできるだけ避け、必要な場合は短く補足してください。\n"
        "過度に抽象的な表現ではなく、「何をする研究か」「何が嬉しいか」が"
        "分かる文章にしてください。\n"
        "難易度は1〜5で、1が易しい、5が非常に難しいという意味です。\n"
        "Abstractだけでは判断しきれない場合は、推測であることが分かる理由にしてください。\n\n"
        f"Title: {paper.title}\n"
        f"Authors: {authors}\n"
        f"Abstract:\n{abstract}"
    )


def _extract_output_text(response_data: dict[str, Any]) -> str:
    candidates = response_data.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise GeminiClientError("Gemini response did not contain candidates")

    first_candidate = candidates[0]
    if not isinstance(first_candidate, dict):
        raise GeminiClientError("Gemini returned unexpected candidate shape")

    content = first_candidate.get("content")
    if not isinstance(content, dict):
        raise GeminiClientError("Gemini response did not contain content")

    parts = content.get("parts")
    if not isinstance(parts, list):
        raise GeminiClientError("Gemini response did not contain parts")

    text_parts = [
        part.get("text")
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    ]
    if not text_parts:
        raise GeminiClientError("Gemini response did not contain output text")
    return "".join(text_parts)


def analyze_paper_abstract(
    paper: PaperResponse,
    model: str,
) -> PaperAIAnalysisCreate:
    settings = get_settings()
    payload = {
        "systemInstruction": {
            "parts": [
                {
                    "text": (
                        "You analyze computer science papers for Japanese "
                        "undergraduate computer science students. Use plain "
                        "Japanese that a student with basic programming, "
                        "algorithms, databases, and machine learning knowledge "
                        "can understand. Avoid unexplained jargon. Return only "
                        "the requested JSON structure."
                    )
                }
            ]
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _build_analysis_prompt(paper)}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseJsonSchema": _analysis_json_schema(),
        },
    }

    try:
        response = get_gemini_client().post(
            f"models/{model}:generateContent",
            params={"key": settings.gemini_api_key},
            json=payload,
        )
        response.raise_for_status()
    except GeminiConfigError:
        raise
    except httpx.HTTPError as error:
        raise GeminiClientError("Gemini analysis request failed") from error

    try:
        response_data = response.json()
        parsed_output = json.loads(_extract_output_text(response_data))
    except (ValueError, TypeError) as error:
        raise GeminiClientError("Gemini returned invalid analysis JSON") from error

    try:
        return PaperAIAnalysisCreate.model_validate(
            {
                "paper_id": paper.id,
                "provider": "gemini",
                "model": model,
                **parsed_output,
                "raw_response": response_data,
            }
        )
    except ValidationError as error:
        raise GeminiClientError("Gemini analysis JSON failed validation") from error
