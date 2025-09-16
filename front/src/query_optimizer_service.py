# src/query_optimizer_service.py
from __future__ import annotations
from typing import Dict, List, Union, Optional
from dotenv import load_dotenv
from openai import OpenAI
import os, json, re

load_dotenv()


class QueryOptimizerService:
    """
    상태 보관 + 원샷 둘 다 지원

    - 상태형:
        svc.update_context(scenario_text=..., generated_logs=...)
        res = svc.make_spl()                 # -> {"query": "<SPL>"}
        spl = svc.get_spl()

    - 원샷(무상태):
        res = svc.make_spl(scenario_text=..., generated_logs=...)
        spl = svc.get_spl(scenario_text=..., generated_logs=...)

    - 호환용:
        svc.ask(...)  # make_spl과 동일
    """

    def __init__(
        self,
        api_key: str,
        model: Optional[str] = None,
        scenario_text: Optional[str] = None,
        generated_logs: Optional[Union[Dict, List[str], str]] = None,
    ):
        if not api_key:
            raise ValueError("OpenAI API key required")
        self.client = OpenAI(api_key=api_key)
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4.1")
        self.scenario_text = scenario_text
        self.generated_logs = generated_logs

    # ---------- 컨텍스트 저장/업데이트 ----------
    def update_context(
        self,
        scenario_text: Optional[str] = None,
        generated_logs: Optional[Union[Dict, List[str], str]] = None,
    ) -> None:
        if scenario_text is not None:
            self.scenario_text = scenario_text
        if generated_logs is not None:
            self.generated_logs = generated_logs

    # ---------- 로그 코퍼스 ----------
    def _logs_to_corpus(self, logs: Optional[Union[Dict, List[str], str]]) -> str:
        if not logs:
            return "(no logs)"
        if isinstance(logs, dict):
            parts: List[str] = []
            for k, v in logs.items():
                if isinstance(v, dict):
                    name = v.get("filename") or v.get("name") or str(k)
                    content = v.get("content", "")
                else:
                    name = str(k)
                    content = str(v)
                parts.append(f"\n# FILE: {name}\n{content}")
            return "".join(parts).strip()
        if isinstance(logs, list):
            return "\n".join(map(str, logs)).strip()
        return str(logs).strip()

    # ---------- 프롬프트 ----------
    def _build_prompt(self, scenario_text: str, corpus: str) -> str:
        return f"""
당신은 Splunk 탐지 엔지니어입니다. 아래 입력을 바탕으로 **Splunk 검색창에 바로 붙여 실행 가능한 SPL**을 만드세요.
반드시 **JSON 한 줄**만 반환합니다. 코드블록/설명/주석 금지.

반환 형식(키 고정):
{{"query":"<SPL 문자열만>"}}

[강제 규칙]
- 쿼리는 반드시 **source="*"** 로 시작한다. (그 뒤에 공백 하나)
- `index=`, `sourcetype=`, `earliest=`, `latest=` 금지.
- 로그가 `Key: Value` 형태라면, **검색/집계 전에 rex로 필요한 필드를 생성**한다.
- 로그 라인의 **브래킷 태그**로 먼저 범위를 좁혀라: 예) "[DLP]", "[USB]", "[EMAIL]", "[FS]" 등.
- 가능한 빠른 연산만 사용: `eval/where/stats/streamstats/timechart` 우선, `transaction/join` 금지.
- 결과 마지막엔 핵심 필드만 남겨 `| table ...` 또는 `| stats ... by ...` 로 정리.

[필드 추출 템플릿(예시 그대로 쓰지 말고 최적화해서 쿼리 재조정 필요)]
- DLP 라인("[DLP] ... Action: ... Channel: ... Policy: ... User: ... Confidence: N%")
  | rex field=_raw "Action:\\s*(?<Action>\\S+)\\s+Channel:\\s*(?<Channel>\\S+)\\s+Policy:\\s*(?<Policy>\\S+)\\s+User:\\s*(?<User>\\S+)\\s+Confidence:\\s*(?<Confidence>\\d+)%"

- USB 라인("[USB] ... Device: ... Event: ... User: ... (FILE: ... SIZE: N)?")
  | rex field=_raw "Device:\\s*(?<Device>\\S+)\\s+Event:\\s*(?<UsbEvent>\\S+)\\s+User:\\s*(?<UsbUser>\\S+)(?:\\s+FILE:\\s*(?<UsbFile>\\S+)\\s+SIZE:\\s*(?<UsbSize>\\d+))?"

- EMAIL 라인("[EMAIL] FROM: ... TO: ... SUBJECT: \"...\" SIZE: N (ATTACHMENT: ...)?")
  | rex field=_raw "FROM:\\s*(?<From>\\S+)\\s+TO:\\s*(?<To>\\S+)\\s+SUBJECT:\\s*\\"(?<Subject>[^\\"]+)\\"\\s+SIZE:\\s*(?<Size>\\d+)(?:\\s+ATTACHMENT:\\s*(?<Attachment>\\S+))?"

- 파일서버 라인("[FS] User: ... Operation: ... File: ... Size: N")
  | rex field=_raw "User:\\s*(?<FsUser>\\S+)\\s+Operation:\\s*(?<FsOp>\\S+)\\s+File:\\s*(?<FsFile>\\S+)\\s+Size:\\s*(?<FsSize>\\d+)"

[시간 정규화(필요 시)]
- CSV/TEXT에 시간 문자열이 있으면 `_time`으로:
  예) `| eval _time=strptime(UtcTime,"%Y-%m-%d %H:%M:%S")`
      `| eval _time=strptime(TimeCreated,"%Y-%m-%dT%H:%M:%S")`
      `| eval _time=strptime(timestamp,"%d/%b/%Y:%H:%M:%S +0000")`


# 시나리오
{scenario_text.strip()}

# 로그(원문)
{corpus}
""".strip()

    # ---------- 자동 교정(LLM 실수 보정) ----------
    def _split_csv(self, s: str) -> List[str]:
        out, cur, quote, esc = [], [], None, False
        for ch in s:
            if quote:
                if esc: cur.append(ch); esc = False
                elif ch == "\\": esc = True
                elif ch == quote: quote = None
                else: cur.append(ch)
            else:
                if ch in ("'", '"'): quote = ch
                elif ch == ",": out.append("".join(cur).strip()); cur = []
                else: cur.append(ch)
        tail = "".join(cur).strip()
        if tail: out.append(tail)
        return [x.strip().strip("'").strip('"') for x in out if x]

    def _rewrite_bad_in(self, field: str, csv: str) -> str:
        items = self._split_csv(csv)
        if not items:
            return f"search {field}=*"
        ors = [
            f'{field}="*{it.strip("*")}*"' if ("*" in it or " " in it or "'" in it)
            else f'{field}="{it}"'
            for it in items
        ]
        return "search " + " OR ".join(ors)

    def _auto_fix(self, spl: str) -> str:
        s = spl.strip()

        def _fix(m: re.Match) -> str:
            fld, csv = m.group(1).strip(), m.group(2).strip()
            if any(ch in csv for ch in ['*', ' ', "'", '"']):
                return self._rewrite_bad_in(fld, csv)
            return m.group(0)

        s = re.sub(r'(?i)\bsearch\s+([A-Za-z0-9_\.]+)\s+IN\s*\(([^)]+)\)', _fix, s)
        s = re.sub(r'(?i)\|\s*stats\b([^\|]+)\|\s*where\s+count\s*>=\s*1\b', r'| stats\1', s)
        s = re.sub(r'(?i)\bsourcetype\s*=\s*"?([A-Za-z0-9_:.-]+)\.log"?', r'sourcetype=\1', s)

        if s.startswith("```"):
            s = "\n".join(ln for ln in s.splitlines() if not ln.strip().startswith("```")).strip()
        return s

    # ---------- 호출 ----------
    def make_spl(
        self,
        scenario_text: Optional[str] = None,
        generated_logs: Optional[Union[Dict, List[str], str]] = None,
        stream: bool = False,
    ) -> Dict[str, str]:
        """
        - 인자를 주면 그 값으로 즉시 실행(원샷)
        - 인자 없으면 self.scenario_text / self.generated_logs 를 사용(상태형)
        """
        scen = (scenario_text if scenario_text is not None else self.scenario_text) or ""
        logs = (generated_logs if generated_logs is not None else self.generated_logs)

        if not scen.strip():
            raise ValueError("scenario_text가 비었습니다. (인자로 전달하거나 update_context로 먼저 설정하세요)")

        corpus = self._logs_to_corpus(logs)
        prompt = self._build_prompt(scen, corpus)

        rsp = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "JSON 한 줄만 출력하세요. 키는 query 하나만."},
                {"role": "user", "content": prompt},
            ],
            stream=stream,
            temperature=0.1,
        )

        if stream:
            buf: List[str] = []
            for ch in rsp:
                piece = getattr(ch.choices[0].delta, "content", None)
                if piece:
                    buf.append(piece)
            content = "".join(buf).strip()
        else:
            content = rsp.choices[0].message.content.strip()

        if content.startswith("```"):
            content = "\n".join(ln for ln in content.splitlines() if not ln.strip().startswith("```")).strip()

        # JSON → {"query": "..."} 정규화
        try:
            obj = json.loads(content)
            q = obj.get("query") if isinstance(obj, dict) else None
            if isinstance(q, str) and q.strip():
                return {"query": self._auto_fix(q)}
        except Exception:
            pass

        # JSON이 아니면 통으로 SPL 본문으로 간주
        return {"query": self._auto_fix(content)}

    # 호환용 별칭
    def ask(
        self,
        scenario_text: Optional[str] = None,
        generated_logs: Optional[Union[Dict, List[str], str]] = None,
        stream: bool = False,
    ) -> Dict[str, str]:
        return self.make_spl(scenario_text=scenario_text, generated_logs=generated_logs, stream=stream)

    def get_spl(
        self,
        scenario_text: Optional[str] = None,
        generated_logs: Optional[Union[Dict, List[str], str]] = None,
        stream: bool = False,
    ) -> str:
        return self.make_spl(scenario_text=scenario_text, generated_logs=generated_logs, stream=stream)["query"]