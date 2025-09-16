#로컬 테스트용
"""
core/explain.py (백엔드 전용)
- SPL(주로 Splunk) 쿼리 파싱 + LLM(OpenAI) 기반 설명/검증
- 테스트 실행 블록 포함 (LLM 전용)

환경변수:
- OPENAI_API_KEY : OpenAI 키
- OPENAI_MODEL   : OpenAI 모델명 (기본 gpt-4o-mini)

주요 함수:
- explain_spl_markdown_backend(spl, include_raw_query=True) -> str
- explain_spl_markdown_backend_with_meta(spl, include_raw_query=True) -> dict
"""

from __future__ import annotations
import os, re
from dotenv import load_dotenv
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

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
# SPL 파서 (단순 파싱만 유지)
# -----------------------------
RE_INDEX = re.compile(r"\bindex\s*=\s*([\w:-]+)")
RE_SOURCETYPE = re.compile(r"\bsourcetype\s*=\s*\"?([\w:.-]+)\"?")
RE_EARLIEST = re.compile(r"\bearliest\s*=\s*([\w@:.+-]+)")
RE_LATEST = re.compile(r"\blatest\s*=\s*([\w@:.+-]+)")
RE_JOIN = re.compile(r"\|\s*join\s+(.+?)\[(.+?)\]", re.I | re.S)

@dataclass
class SplOverview:
    index: List[str] = field(default_factory=list)
    sourcetype: List[str] = field(default_factory=list)
    time_window: Dict[str, str] = field(default_factory=dict)

@dataclass
class SplOps:
    joins: List[Dict[str, str]] = field(default_factory=list)
    others: List[str] = field(default_factory=list)

def parse_spl(spl: str) -> Dict[str, Any]:
    """간단히 index/sourcetype/time_window/joins 정도만 파싱"""
    text = spl.strip()
    ov = SplOverview()
    ops = SplOps()

    ov.index = RE_INDEX.findall(text)
    ov.sourcetype = RE_SOURCETYPE.findall(text)
    e = RE_EARLIEST.search(text)
    l = RE_LATEST.search(text)
    if e: ov.time_window["earliest"] = e.group(1)
    if l: ov.time_window["latest"] = l.group(1)

    for m in RE_JOIN.finditer(text):
        ops.joins.append({"on": m.group(1).strip(), "subsearch": m.group(2).strip()})

    return {"overview": ov, "ops": ops}

# -----------------------------
# LLM 템플릿
# -----------------------------
_LLM_SYSTEM = (
    "당신은 Splunk SPL 쿼리 설명 및 검증 전문가입니다. "
    "입력된 SPL을 절대 실행하지 말고, 구조를 분석해 고정된 섹션의 Markdown을 만듭니다. "
    "추측 금지: 알 수 없는 부분은 '확실하지 않음'으로 표기합니다. "
    "반드시 섹션 순서와 제목을 지키고, 불필요한 수사는 금지합니다. 한국어로 답변합니다."
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
    "### 검증 결과\n- ...\n"
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
        out = getattr(rsp, "output_text", None)
        if out:
            return out.strip(), None
    except Exception as e1:
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
# 퍼사드
# -----------------------------
def _prepend_raw_query(
    spl: str, body: str, engine: str, model: str, llm_error: Optional[str] = None
) -> str:
    head = f"<!-- engine={engine}; model={model}{'; error='+llm_error if llm_error else ''} -->\n"
    raw = f"### 입력된 쿼리\n```spl\n{spl}\n```\n\n"
    return head + raw + body

def explain_spl_markdown_backend_with_meta(
    spl: str,
    include_raw_query: bool = True
) -> Dict[str, Any]:
    out, llm_error = llm_explain_and_validate(spl)
    engine = "LLM" if out else "ERROR"
    if not out:
        out = f"LLM 호출 실패: {llm_error}"

    if include_raw_query:
        out = _prepend_raw_query(spl, out, engine, OPENAI_MODEL, llm_error)

    return {
        "engine": engine,
        "model": OPENAI_MODEL,
        "llm_ready": is_llm_ready(),
        "llm_error": llm_error,
        "markdown": out,
    }

def explain_spl_markdown_backend(
    spl: str,
    include_raw_query: bool = True
) -> str:
    return explain_spl_markdown_backend_with_meta(
        spl, include_raw_query=include_raw_query
    )["markdown"]

# -----------------------------
# 실행 테스트 (LLM 전용)
# -----------------------------
if __name__ == "__main__":
    test_query = r'''(index=main sourcetype="web:access" earliest=-24h latest=now)
| rex field=uri "(?i)(?<sqlinj>UNION|SELECT|--|OR 1=1)"
| lookup threat_ip ip AS src_ip OUTPUT risk_level
| eval sqli_flag=if(isnotnull(sqlinj),1,0)
| stats count AS total_requests, sum(sqli_flag) AS sqli_hits BY src_ip, user_agent
| where sqli_hits>=5
| timechart span=1h count BY user_agent
| sort - total_requests
| dedup src_ip
| table _time, src_ip, user_agent, total_requests, sqli_hits, risk_level
'''
    print("\n===== BACKEND TEST (LLM only) =====\n")
    if not is_llm_ready():
        print("⚠️ OpenAI API key가 설정되지 않았습니다.")
    else:
        meta = explain_spl_markdown_backend_with_meta(test_query, include_raw_query=True)
        print(f"[engine={meta['engine']}] [model={meta['model']}] [llm_ready={meta['llm_ready']}] [err={meta['llm_error']}]")
        print(meta["markdown"])

__all__ = [
    "parse_spl",
    "is_llm_ready",
    "llm_explain_and_validate",
    "explain_spl_markdown_backend",
    "explain_spl_markdown_backend_with_meta",
]
