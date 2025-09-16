import streamlit as st
from openai import OpenAI
import os
import pandas as pd
from io import StringIO
from dotenv import load_dotenv
import base64

# 환경 변수 로드
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 페이지 기본 설정 (wide 모드)
st.set_page_config(page_title="SPLearn - AI Security Trainer", page_icon="🛡️", layout="wide")
st.title("🛡️ SPLearn - AI Security Trainer")

# ───────────────────────────────
# 입력칸
scenario = st.text_area("✍️ 공격 시나리오를 입력하세요", height=150)

# 입력칸 밑에 버튼 + 로딩 상태 같은 줄 배치
btn_col, spinner_col = st.columns([1, 4])
with btn_col:
    generate_btn = st.button("🚀 생성하기")
with spinner_col:
    status_placeholder = st.empty()

st.markdown("---")

# ───────────────────────────────
# 하단 레이아웃 (좌: 로그 / 우: 룰 + 설명)
left_col, right_col = st.columns([2, 2])

with left_col:
    st.markdown("## 📄 로그 생성 결과 (상위 10개)")
    log_placeholder = st.empty()
    download_placeholder = st.empty()
    if "log_ready" not in st.session_state:
        log_placeholder.info("👉 로그가 여기에 출력될 예정입니다.")

with right_col:
    st.markdown("## 🔎 Splunk 탐지 룰")
    rule_placeholder = st.empty()
    if "rule_ready" not in st.session_state:
        rule_placeholder.info("👉 Splunk 탐지 룰이 여기에 표시됩니다.")

    st.markdown("## 📝 룰 셋 설명")
    explain_placeholder = st.empty()
    if "explain_ready" not in st.session_state:
        explain_placeholder.info("👉 룰 설명이 여기에 표시됩니다.")

# ───────────────────────────────
# 버튼 클릭 시 처리
if generate_btn and scenario:
    with status_placeholder, st.spinner("AI가 로그와 탐지 룰을 생성 중입니다..."):
        print("[DEBUG] 시나리오 입력 받음:", scenario)

        # 1. 로그 생성
        print("[DEBUG] 로그 생성 요청 시작")
        log_prompt = f"""
        다음 공격 시나리오에 맞는 보안 로그를 20줄 CSV 형식으로 생성해줘.
        CSV 컬럼: timestamp, src_ip, dst_ip, action, detail
        시나리오: {scenario}
        """
        log_resp = client.responses.create(model="gpt-5", input=log_prompt)
        log_text = log_resp.output_text.strip()
        print("[DEBUG] 로그 생성 완료\n", log_text[:300], "...")  # 앞부분만 출력

        try:
            df = pd.read_csv(StringIO(log_text))
            print("[DEBUG] CSV 파싱 성공, shape:", df.shape)
        except Exception as e:
            print("[DEBUG] CSV 파싱 실패, fallback 사용:", e)
            df = pd.DataFrame({"raw_log": log_text.splitlines()})

        # 세션에 저장
        st.session_state["log_ready"] = True
        st.session_state["log_df"] = df

        # 로그 출력
        log_placeholder.dataframe(df.head(10), width="stretch")

        # CSV 다운로드 (Base64 링크 방식 → 코드 멈춤 방지)
        csv_str = df.to_csv(index=False)
        b64 = base64.b64encode(csv_str.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="synthetic_logs.csv">⬇️ CSV 다운로드</a>'
        download_placeholder.markdown(href, unsafe_allow_html=True)

        # 2. Splunk 탐지 룰
        print("[DEBUG] Splunk 룰 생성 요청 시작")
        rule_prompt = f"다음 시나리오에 대한 Splunk SPL 탐지 쿼리를 만들어줘.\n시나리오: {scenario}"
        rule_resp = client.responses.create(model="gpt-5", input=rule_prompt)
        rule_text = rule_resp.output_text.strip()
        print("[DEBUG] 룰 생성 완료\n", rule_text)

        st.session_state["rule_ready"] = True
        st.session_state["rule_text"] = rule_text

        # ✅ 고정 크기 + 스크롤 가능
        rule_placeholder.markdown(
            f"""
            <div style='width:100%; height:400px; overflow:auto;
                        padding:15px; font-size:15px;
                        background-color:#f8f9fa; border-radius:5px;
                        white-space: pre-wrap; word-wrap: break-word;'>
                {rule_text}
            </div>
            """,
            unsafe_allow_html=True
        )

        # 3. 룰 설명
        print("[DEBUG] 룰 설명 요청 시작")
        explain_prompt = f"다음 Splunk 탐지 쿼리의 각 부분이 어떤 역할을 하는지 설명해줘:\n{rule_text}"
        explain_resp = client.responses.create(model="gpt-5", input=explain_prompt)
        explain_text = explain_resp.output_text.strip()
        print("[DEBUG] 룰 설명 완료\n", explain_text[:300], "...")  # 앞부분만 출력

        st.session_state["explain_ready"] = True
        st.session_state["explain_text"] = explain_text

        # ✅ 고정 크기 + 스크롤 가능
        explain_placeholder.markdown(
            f"""
            <div style='width:100%; height:400px; overflow:auto;
                        border:1px solid #ddd; border-radius:5px;
                        padding:15px; font-size:15px;
                        white-space: pre-wrap; word-wrap: break-word;'>
                {explain_text}
            </div>
            """,
            unsafe_allow_html=True
        )

    status_placeholder.empty()
    print("[DEBUG] 전체 프로세스 완료 ✅")