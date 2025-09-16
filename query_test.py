"""
core/explain.py (백엔드 전용)
- SPL(주로 Splunk) 쿼리 파싱 + 고정 형식의 Markdown 설명 생성
- 쿼리 전체 요약(summarize) + 유효성 검증(validate)
- LLM(OpenAI) 기반 설명/검증을 옵션으로 지원 (요청대로 GPT API 사용)
- 표준 라이브러리 + (선택) openai 패키지

환경변수:
- OPENAI_API_KEY: OpenAI 키 (없으면 규칙 기반만 동작)
- OPENAI_MODEL : OpenAI 모델명(기본 gpt-4o-mini)

사용 예:
    from core.explain import explain_spl_markdown_backend
    md = explain_spl_markdown_backend(SPL_STRING, prefer_gpt=True)
    open("explain.md", "w", encoding="utf-8").write(md)
"""
from __future__ import annotations
import os
from dotenv import load_dotenv
import re
from dataclasses import dataclass, field
from typing import List, Dict, Any, Tuple, Optional

load_dotenv()

# -----------------------------
# 0) (선택) OpenAI 클라이언트
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
# 1) 토큰 추출 정규식
# -----------------------------
RE_INDEX = re.compile(r"\bindex\s*=\s*([\w:-]+)")
RE_SOURCETYPE = re.compile(r"\bsourcetype\s*=\s*\"?([\w:.-]+)\"?")
RE_EARLIEST = re.compile(r"\bearliest\s*=\s*([\w@:.+-]+)")
RE_LATEST = re.compile(r"\blatest\s*=\s*([\w@:.+-]+)")
RE_SEARCH_TERM = re.compile(r"\|\s*search\s+(.+?)(?=\|\s*\w+|$)", re.I | re.S)
RE_TRANSACTION = re.compile(r"\|\s*transaction\s+([^|]+)", re.I)
RE_STATS = re.compile(r"\|\s*stats\s+(.+?)(?=\|\s*\w+|$)", re.I | re.S)
RE_TIMECHART = re.compile(r"\|\s*timechart\s+(.+?)(?=\|\s*\w+|$)", re.I | re.S)
RE_EVAL = re.compile(r"\|\s*eval\s+(.+?)(?=\|\s*\w+|$)", re.I | re.S)
RE_WHERE = re.compile(r"\|\s*where\s+(.+?)(?=\|\s*\w+|$)", re.I | re.S)
RE_TABLE = re.compile(r"\|\s*table\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_FIELDS = re.compile(r"\|\s*fields\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_SORT = re.compile(r"\|\s*sort\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_DEDUP = re.compile(r"\|\s*dedup\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_LOOKUP = re.compile(r"\|\s*lookup\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_REX = re.compile(r"\|\s*rex\s+(.+?)(?=\|\s*\w+|$)", re.I)
RE_JOIN = re.compile(r"\|\s*join\s+(.+?)\[(.+?)\]", re.I | re.S)

# -----------------------------
# 2) 데이터 구조
# -----------------------------
@dataclass
class SplOverview:
    index: List[str] = field(default_factory=list)
    sourcetype: List[str] = field(default_factory=list)
    time_window: Dict[str, str] = field(default_factory=dict)  # earliest/latest

@dataclass
class SplOps:
    search_terms: List[str] = field(default_factory=list)
    evals: List[str] = field(default_factory=list)
    transactions: List[str] = field(default_factory=list)
    stats: List[str] = field(default_factory=list)
    timecharts: List[str] = field(default_factory=list)
    wheres: List[str] = field(default_factory=list)
    joins: List[Dict[str, str]] = field(default_factory=list)  # {on:..., subsearch:...}
    lookups: List[str] = field(default_factory=list)
    rexes: List[str] = field(default_factory=list)
    sorts: List[str] = field(default_factory=list)
    dedups: List[str] = field(default_factory=list)
    tables: List[str] = field(default_factory=list)
    fields_cmds: List[str] = field(default_factory=list)
    others: List[str] = field(default_factory=list)

# -----------------------------
# 3) 파서
# -----------------------------
def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip())

essential_cmds = [
    "search","eval","transaction","stats","timechart","where",
    "lookup","rex","join","sort","dedup","table","fields"
]

def parse_spl(spl: str) -> Dict[str, Any]:
    text = spl.strip()
    ov = SplOverview()
    ops = SplOps()

    ov.index = RE_INDEX.findall(text)
    ov.sourcetype = RE_SOURCETYPE.findall(text)
    e = RE_EARLIEST.search(text)
    l = RE_LATEST.search(text)
    if e: ov.time_window['earliest'] = e.group(1)
    if l: ov.time_window['latest'] = l.group(1)

    for m in RE_JOIN.finditer(text):
        ops.joins.append({'on': _norm_ws(m.group(1)), 'subsearch': _norm_ws(m.group(2))})

    patterns = [
        (RE_SEARCH_TERM, ops.search_terms), (RE_EVAL, ops.evals),
        (RE_TRANSACTION, ops.transactions), (RE_STATS, ops.stats),
        (RE_TIMECHART, ops.timecharts), (RE_WHERE, ops.wheres),
        (RE_LOOKUP, ops.lookups), (RE_REX, ops.rexes), (RE_SORT, ops.sorts),
        (RE_DEDUP, ops.dedups), (RE_TABLE, ops.tables), (RE_FIELDS, ops.fields_cmds),
    ]
    for pat, bucket in patterns:
        for m in pat.finditer(text):
            bucket.append(_norm_ws(m.group(1)))

    # 기타: 파이프 단위 세그먼트에서 인지 못한 커맨드 수집
    for seg in re.split(r"\|", text)[1:]:
        seg = seg.strip()
        if not seg:
            continue
        first = seg.split()[0].lower() if seg.split() else ""
        if first not in essential_cmds:
            ops.others.append(seg)

    return {'overview': ov, 'ops': ops}

# -----------------------------
# 4) 의도 추정(휴리스틱)
# -----------------------------
INTENT_RULES = [
    (re.compile(r"event_id\s*=\s*4688.*powershell", re.I | re.S), "PowerShell 실행 탐지"),
    (re.compile(r"transaction.+4625.+4624.+4688", re.I | re.S), "로그인 실패→성공 후 프로세스 실행 연쇄"),
    (re.compile(r"sqli|information_schema|OR 1=1|sqlmap", re.I), "SQLi/인증우회 시도 탐지"),
    (re.compile(r"7z\.exe|invoke-webrequest|exfil|net_dst", re.I), "압축 및 외부 전송 행위 탐지"),
]

def infer_intent(spl: str) -> str:
    for rx, label in INTENT_RULES:
        if rx.search(spl):
            return label
    return "일반 로그 필터/집계 쿼리"

# -----------------------------
# 5) 요약 & 검증 (규칙 기반)
# -----------------------------
def summarize_spl(parsed: Dict[str, Any], spl: str) -> str:
    ov: SplOverview = parsed['overview']
    ops: SplOps = parsed['ops']
    intent = infer_intent(spl)

    srcs = []
    if ov.index: srcs.append(f"index={','.join(sorted(set(ov.index)))}")
    if ov.sourcetype: srcs.append(f"sourcetype={','.join(sorted(set(ov.sourcetype)))}")
    src_txt = (" / ".join(srcs)) if srcs else "데이터 소스 미지정"

    steps = []
    if ops.search_terms: steps.append("기본 검색어 적용")
    if ops.evals: steps.append("eval 계산")
    if ops.transactions: steps.append("transaction으로 이벤트 연계")
    if ops.stats: steps.append("stats 집계")
    if ops.timecharts: steps.append("timechart 시계열 집계")
    if ops.joins: steps.append("join + subsearch 결합")
    if ops.rexes: steps.append("rex 정규식 추출")
    if ops.lookups: steps.append("lookup 참조")
    if ops.sorts: steps.append("sort 정렬")
    if ops.dedups: steps.append("dedup 중복 제거")
    if ops.tables or ops.fields_cmds: steps.append("table/fields로 출력 필드 지정")
    if not steps:
        steps.append("단순 필터/기본 검색")

    return (
        f"이 쿼리는 {src_txt} 에서 데이터를 조회하며, "
        f"{' → '.join(steps)} 을(를) 수행합니다. 의도: {intent}"
    )

def validate_spl(parsed: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    ov: SplOverview = parsed['overview']
    ops: SplOps = parsed['ops']

    if not ov.index and not ov.sourcetype:
        warnings.append("데이터 소스(index/sourcetype) 미지정")
    if 'earliest' not in ov.time_window and 'latest' not in ov.time_window:
        warnings.append("시간 범위(earliest/latest) 미지정 → 대용량 검색 위험")
    if ops.joins:
        warnings.append("join 사용 → 대규모 데이터에서 성능 저하 가능. 키 정합성과 선필터 권장")
    if ops.transactions:
        warnings.append("transaction 사용 → 리소스 소모 큼. 대안(stats/correlation) 검토")
    if not (ops.tables or ops.fields_cmds):
        warnings.append("출력 필드(table/fields) 미지정 → 결과 해석 어려움")
    if ops.wheres:
        has_numeric = any(re.search(r"(>=|<=|>\s*\d|<\s*\d|=\s*\d)", w) for w in ops.wheres)
        if not has_numeric:
            warnings.append("where에 수치 임계 조건 부재 → 탐지 기준 불명확 가능")
    return warnings

# -----------------------------
# 6) 고정 템플릿 Markdown(규칙 기반)
# -----------------------------
def _mk_md_base(parsed: Dict[str, Any], spl: str) -> str:
    ov: SplOverview = parsed['overview']
    ops: SplOps = parsed['ops']
    intent = infer_intent(spl)

    idx = ", ".join(sorted(set(ov.index))) or "(명시 없음)"
    stype = ", ".join(sorted(set(ov.sourcetype))) or "(명시 없음)"
    twin = []
    if 'earliest' in ov.time_window: twin.append(f"earliest={ov.time_window['earliest']}")
    if 'latest' in ov.time_window: twin.append(f"latest={ov.time_window['latest']}")
    twin_str = ", ".join(twin) if twin else "(명시 없음)"

    base_filters: List[str] = []
    if ops.search_terms: base_filters.append(ops.search_terms[0])
    if ops.wheres: base_filters.extend(ops.wheres)

    steps: List[str] = []
    for name, items in [
        ("eval", ops.evals), ("transaction", ops.transactions), ("stats", ops.stats),
        ("timechart", ops.timecharts),
        ("join", [f"on {j['on']} | subsearch: {j['subsearch']}" for j in ops.joins]),
        ("lookup", ops.lookups), ("rex", ops.rexes), ("sort", ops.sorts),
        ("dedup", ops.dedups), ("table", ops.tables or ops.fields_cmds), ("other", ops.others),
    ]:
        for it in items:
            steps.append(f"- **{name}**: {it}")

    tuning: List[str] = []
    m = re.search(r"transaction[^|]*maxspan\s*=\s*([\w:]+)", spl, re.I)
    if m: tuning.append(f"transaction maxspan={m.group(1)} (환경에 맞게 조정)")
    for w in ops.wheres:
        if re.search(r">=|<=|>\s|<\s|=\s*\d", w):
            tuning.append(f"where 임계 확인: {w}")
    for s in ops.stats:
        if re.search(r"count\s+as\s+\w+", s, re.I):
            tuning.append("stats 기반 임계(건수) 검토")

    fp: List[str] = []
    if 'powershell' in spl.lower(): fp.append("관리 스크립트에 의한 PowerShell 실행")
    if re.search(r"sqlmap|OR 1=1|UNION", spl, re.I): fp.append("모의 스캔/QA 테스트 트래픽")
    if re.search(r"7z|invoke-webrequest|wget|curl", spl, re.I): fp.append("백업/로그 수집과 혼동")
    if not fp: fp.append("운영 자동화/배치 작업과의 혼동 가능")

    out_fields = ", ".join(ops.tables[:1] or ops.fields_cmds[:1]) if (ops.tables or ops.fields_cmds) else "(table/fields 미지정)"

    md = []
    md.append(f"### 요약 Intent\n- {intent}")
    md.append(f"### 데이터 소스\n- index: {idx}\n- sourcetype: {stype}\n- 시간범위: {twin_str}")
    md.append("### 기본 필터\n- " + ("\n- ".join(base_filters) if base_filters else "(검색어/where 미지정)"))
    md.append("### 연산 단계\n" + ("\n".join(steps) if steps else "- (연산 미검출)"))
    md.append("### 임계/튜닝 포인트\n- " + ("\n- ".join(tuning) if tuning else "(특이 임계 없음)"))
    md.append("### 오탐 가능성\n- " + "\n- ".join(fp))
    md.append(f"### 출력/결과 필드\n- {out_fields}")
    return "\n\n".join(md)

# -----------------------------
# 7) LLM 기반 설명/검증 생성
# -----------------------------
_LLM_SYSTEM = (
    "당신은 Splunk SPL 쿼리 설명 및 검증 전문가입니다. "
    "입력된 SPL을 절대 실행하지 말고, 구조를 분석해 고정된 섹션의 Markdown을 만듭니다. "
    "추측 금지: 알 수 없는 부분은 '확실하지 않음'으로 표기합니다. "
    "반드시 섹션 순서와 제목을 지키고, 불필요한 수사는 금지합니다. 한국어로 답변합니다."
)

_LLM_TEMPLATE = (
    "다음은 SPL입니다:\n```spl\n{spl}\n```\n"
    "요구 출력 형식(반드시 이 순서/제목):\n"
    "### 쿼리 전체 설명\n- <한 문장 요약>\n\n"
    "### 요약 Intent\n- <의도>\n\n"
    "### 데이터 소스\n- index: <값 또는 (명시 없음)>\n- sourcetype: <값 또는 (명시 없음)>\n- 시간범위: <earliest/latest 또는 (명시 없음)>\n\n"
    "### 기본 필터\n- <search/where 요약 없으면 (검색어/where 미지정)>\n\n"
    "### 연산 단계\n- **eval**: <항목>\n- **transaction**: <항목>\n- **stats**: <항목>\n- **timechart**: <항목>\n- **join**: <항목>\n- **lookup**: <항목>\n- **rex**: <항목>\n- **sort**: <항목>\n- **dedup**: <항목>\n- **table**: <항목>\n- **other**: <항목>\n\n"
    "### 임계/튜닝 포인트\n- <없으면 (특이 임계 없음)>\n\n"
    "### 오탐 가능성\n- <항목들>\n\n"
    "### 출력/결과 필드\n- <table/fields 또는 (미지정)>\n\n"
    "### 검증 결과\n- <경고 목록 또는 '특별한 경고 없음'>\n"
)

def is_llm_ready() -> bool:
    return _OPENAI is not None

def llm_explain_and_validate(spl: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Returns: (markdown or None, error_message or None)
    1) Responses API (system + string input)
    2) Responses API (messages 배열)
    3) Chat Completions
    """
    if _OPENAI is None:
        return None, "OPENAI_API_KEY not set"

    prompt = _LLM_TEMPLATE.format(spl=spl)
    # 1) Responses API (system + input string)
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
        # 호환성 처리
        parts = []
        for item in getattr(rsp, "output", []) or []:
            for c in getattr(item, "content", []) or []:
                if getattr(c, "type", "") == "output_text":
                    parts.append(getattr(c, "text", ""))
        if parts:
            return "\n".join(parts).strip(), None
    except Exception as e1:
        # 2) Responses API (messages 배열)
        try:
            rsp = _OPENAI.responses.create(
                model=OPENAI_MODEL,
                input=[
                    {"role": "system", "content": _LLM_SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )
            out = getattr(rsp, "output_text", None)
            if out:
                return out.strip(), None
        except Exception as e2:
            # 3) Chat Completions
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
            except Exception as e3:
                return None, f"{type(e1).__name__} / {type(e2).__name__} / {type(e3).__name__}"

    return None, "Unknown response format"

# -----------------------------
# 8) 퍼사드
# -----------------------------
def explain_spl_to_markdown(spl: str) -> str:
    parsed = parse_spl(spl)
    return _mk_md_base(parsed, spl)

def explain_spl_to_markdown_full(spl: str) -> str:
    parsed = parse_spl(spl)
    summary = summarize_spl(parsed, spl)
    base_md = _mk_md_base(parsed, spl)
    warnings = validate_spl(parsed)
    md = []
    md.append("### 쿼리 전체 설명\n- " + summary)
    md.append(base_md)
    if warnings:
        md.append("### 검증 결과\n- " + "\n- ".join(warnings))
    else:
        md.append("### 검증 결과\n- 특별한 경고 없음")
    return "\n\n".join(md)

def _prepend_raw_query(spl: str, body: str, engine: str, model: str, llm_error: Optional[str]=None) -> str:
    head = f"<!-- engine={engine}; model={model}{'; error='+llm_error if llm_error else ''} -->\n"
    raw = f"### 입력된 쿼리\n```spl\n{spl}\n```\n\n"
    return head + raw + body

def explain_spl_markdown_backend_with_meta(
    spl: str,
    prefer_gpt: bool = True,
    include_raw_query: bool = True
) -> Dict[str, Any]:
    """메타정보 포함 버전: 엔진/모델/에러를 함께 반환"""
    used_engine = "RULE"
    llm_error: Optional[str] = None
    out: Optional[str] = None

    if prefer_gpt and _OPENAI is not None:
        out, llm_error = llm_explain_and_validate(spl)
        if out:
            used_engine = "LLM"

    if not out:
        out = explain_spl_to_markdown_full(spl)

    if include_raw_query:
        out = _prepend_raw_query(spl, out, used_engine, OPENAI_MODEL, llm_error)

    return {
        "engine": used_engine,
        "model": OPENAI_MODEL,
        "llm_ready": is_llm_ready(),
        "llm_error": llm_error,
        "markdown": out,
    }

def explain_spl_markdown_backend(
    spl: str,
    prefer_gpt: bool = True,
    include_raw_query: bool = True
) -> str:
    """기존 호환 반환(문자열). 내부에서 엔진/모델 주석 + 입력 쿼리 포함."""
    meta = explain_spl_markdown_backend_with_meta(
        spl, prefer_gpt=prefer_gpt, include_raw_query=include_raw_query
    )
    return meta["markdown"]

# -----------------------------
# 9) 간단 실행 테스트
# -----------------------------
if __name__ == "__main__":
    spl1 = r'''(index=main sourcetype="web:access" earliest=-24h latest=now)
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
    print("\n===== BACKEND (prefer_gpt=True) =====\n")
    meta = explain_spl_markdown_backend_with_meta(spl1, prefer_gpt=True, include_raw_query=True)
    print(f"[engine={meta['engine']}] [model={meta['model']}] [llm_ready={meta['llm_ready']}] [err={meta['llm_error']}]")
    print(meta["markdown"])

__all__ = [
    'parse_spl',
    'infer_intent',
    'summarize_spl',
    'validate_spl',
    'explain_spl_to_markdown',
    'explain_spl_to_markdown_full',
    'explain_spl_markdown_backend',
    'explain_spl_markdown_backend_with_meta',
    'is_llm_ready',
    'llm_explain_and_validate',
]
