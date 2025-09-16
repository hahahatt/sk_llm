#모듈화
"""
core/explain.py
- SPL(주로 Splunk) 쿼리 파싱 및 설명 모듈
- LLM(OpenAI) 기반 설명/검증만 지원 (규칙 기반 제거)

환경변수:
- OPENAI_API_KEY : OpenAI 키
- OPENAI_MODEL   : OpenAI 모델명 (기본값: gpt-4o-mini)

주요 함수:
- explain_spl_markdown_backend(spl, include_raw_query=True) -> str
- explain_spl_markdown_backend_with_meta(spl, include_raw_query=True) -> dict
"""

from __future__ import annotations
import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional, Tuple

load_dotenv()

# -----------------------------
# OpenAI 클라이언트
# -----------------------------
_OPENAI = None
try:
    if os.getenv("OPENAI_API_KEY"):
        from openai import OpenAI  # pip install openai>=1.0.0
        _OPENAI = OpenAI()
except Exception:
    _OPENAI = None

OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# -----------------------------
# LLM 템플릿
# -----------------------------
_LLM_SYSTEM = (
    "당신은 Splunk SPL 쿼리 설명 및 검증 전문가입니다. "
    "입력된 SPL을 절대 실행하지 말고, 구조를 분석해 고정된 섹션의 Markdown을 만듭니다. "
    "추측 금지: 알 수 없는 부분은 '확실하지 않음'으로 표기합니다. "
    "섹션 순서/제목은 반드시 유지하세요."
)

_LLM_TEMPLATE = (
    "다음은 SPL입니다:\n```spl\n{spl}\n```\n"
    "요구 출력 형식:\n"
    "### 쿼리 전체 설명\n- <요약>\n\n"
    "### 요약 Intent\n- <의도>\n\n"
    "### 데이터 소스\n- index: ...\n- sourcetype: ...\n- 시간범위: ...\n\n"
    "### 기본 필터\n- ...\n\n"
    "### 연산 단계\n- **eval**: ...\n- **transaction**: ...\n- **stats**: ...\n"
    "- **timechart**: ...\n- **join**: ...\n- **lookup**: ...\n- **rex**: ...\n"
    "- **sort**: ...\n- **dedup**: ...\n- **table**: ...\n- **other**: ...\n\n"
    "### 임계/튜닝 포인트\n- ...\n\n"
    "### 오탐 가능성\n- ...\n\n"
    "### 출력/결과 필드\n- ...\n\n"
    "### 쿼리 검증\n- <검증>\n"
)

# -----------------------------
# LLM 호출
# -----------------------------
def is_llm_ready() -> bool:
    return _OPENAI is not None

def llm_explain_and_validate(spl: str) -> Tuple[Optional[str], Optional[str]]:
    if _OPENAI is None:
        return None, "OPENAI_API_KEY not set"

    prompt = _LLM_TEMPLATE.format(spl=spl)
    try:
        rsp = _OPENAI.responses.create(
            model=OPENAI_MODEL,
            input=prompt,
            system=_LLM_SYSTEM,
            temperature=0.2,
        )
        if hasattr(rsp, "output_text") and rsp.output_text:
            return rsp.output_text.strip(), None
    except Exception as e:
        try:
            chat = _OPENAI.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            return chat.choices[0].message.content.strip(), None
        except Exception as e2:
            return None, str(e2)
    return None, "Unknown response format"

# -----------------------------
# 퍼사드 함수
# -----------------------------
def _prepend_raw_query(spl: str, body: str, model: str, err: Optional[str]=None) -> str:
    head = f"<!-- engine=LLM; model={model}{'; error='+err if err else ''} -->\n"
    raw = f"### 입력된 쿼리\n```spl\n{spl}\n```\n\n"
    return head + raw + body

def explain_spl_markdown_backend_with_meta(
    spl: str,
    include_raw_query: bool = True
) -> Dict[str, Any]:
    out, error = llm_explain_and_validate(spl)
    if not out:
        raise RuntimeError(f"LLM failed: {error}")

    if include_raw_query:
        out = _prepend_raw_query(spl, out, OPENAI_MODEL, error)

    return {
        "engine": "LLM",
        "model": OPENAI_MODEL,
        "llm_ready": is_llm_ready(),
        "llm_error": error,
        "markdown": out,
    }

def explain_spl_markdown_backend(
    spl: str,
    include_raw_query: bool = True
) -> str:
    return explain_spl_markdown_backend_with_meta(
        spl, include_raw_query=include_raw_query
    )["markdown"]

__all__ = [
    "is_llm_ready",
    "llm_explain_and_validate",
    "explain_spl_markdown_backend",
    "explain_spl_markdown_backend_with_meta",
]