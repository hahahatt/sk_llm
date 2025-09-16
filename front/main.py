#!/usr/bin/env python3
"""
시나리오 기반 다중 로그 생성기 - 메인 애플리케이션
"""

import streamlit as st
import os
from datetime import datetime
import zipfile
import io

from src.nlp_processor import NLPProcessor
from src.scenario_manager import ScenarioManager
from src.log_generator import LogGenerator
from src.download_manager import DownloadManager
from dotenv import load_dotenv

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from back.query_test import proccess_spl_markdown
from back.explain import explain_spl_markdown_backend


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

def main():
    st.set_page_config(
        page_title="시나리오 기반 다중 로그 생성기",
        page_icon="🚀",
        layout="wide"
    )
    
    # 사이드바 - API 키 설정
    with st.sidebar:
        st.header("🔑 설정")
        # api_key = st.text_input("OpenAI API Key", type="password", help="OpenAI API 키를 입력하세요")
        
        # #if api_key:
        #     st.success("✅ API 키 설정됨")
        # else:
        #     st.warning("⚠️ API 키를 입력해주세요")
        
        st.divider()
        st.header("📊 생성 설정")
        log_count = st.number_input("로그 개수 (파일당)", min_value=100, max_value=10000, value=1000, step=100)
    
    # 메인 헤더
    st.title("🚀 시나리오 기반 다중 로그 생성기")
    st.markdown("**하나의 시나리오에서 연관된 여러 종류의 로그를 동시에 생성합니다**")

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    # 초기화
    if not api_key:
        st.error("먼저 사이드바에서 OpenAI API 키를 입력해주세요.")
        return
    
    # 컴포넌트 초기화
    nlp_processor = NLPProcessor(api_key)
    scenario_manager = ScenarioManager()
    log_generator = LogGenerator()
    download_manager = DownloadManager()
    
    # 탭 구성
    tab1, tab2, tab3 = st.tabs(["📝 시나리오 입력", "📋 샘플 시나리오", "📥 생성된 로그"])
    
    with tab1:
        st.header("📝 자연어 시나리오 입력")
        
        scenario_input = st.text_area(
            "시나리오를 자연어로 설명해주세요",
            placeholder="예: 웹서버에 대한 외부 침입 공격 시나리오를 생성해주세요. 공격자가 SQL 인젝션을 통해 관리자 계정을 탈취하고 내부 데이터베이스에서 고객 정보를 빼내는 상황입니다.",
            height=150
        )
        
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("🔄 시나리오 분석 및 구체화", type="primary", use_container_width=True):
                if scenario_input.strip():
                    with st.spinner("AI가 시나리오를 분석하고 구체화하는 중..."):
                        try:
                            processed_scenario = nlp_processor.process_scenario(scenario_input)
                            st.session_state['processed_scenario'] = processed_scenario
                            st.success("✅ 시나리오 분석 완료!")
                        except Exception as e:
                            st.error(f"❌ 시나리오 분석 실패: {str(e)}")
                else:
                    st.warning("시나리오를 입력해주세요.")
        
        with col2:
            if st.button("🚀 로그 생성", type="secondary", use_container_width=True):
                if 'processed_scenario' in st.session_state:
                    generate_logs(st.session_state['processed_scenario'], log_generator, log_count)
                else:
                    st.warning("먼저 시나리오를 분석해주세요.")

        with col3:
            if st.button("🔎 SPL 룰 생성 및 검증", type="secondary", use_container_width=True):
                if 'processed_scenario' in st.session_state:
                    with st.spinner("AI가 SPL 룰을 생성하고 검증하는 중..."):
                        try:
                            # 👉 process_spl_markdown 함수 사용
                            spl_result = explain_spl_markdown_backend(test_query)
                            st.session_state['spl_result'] = spl_result
                            st.success("✅ SPL 룰 생성 및 검증 완료!")
                        except Exception as e:
                            st.error(f"❌ SPL 룰 생성 실패: {str(e)}")
                else:
                    st.warning("먼저 시나리오를 분석해주세요.")
        
        # 처리된 시나리오 표시
        if 'processed_scenario' in st.session_state:
            display_processed_scenario(st.session_state['processed_scenario'])
        
        # if 'spl_result' in st.session_state:
        #     st.subheader("📜 생성된 SPL 룰 및 검증 결과")
        #     st.markdown(
        #         f"<div style='max-height:400px; overflow-y:auto; "
        #         f"background-color:#f8f9fa; padding:15px; border-radius:5px;'>"
        #         f"{st.session_state['spl_result']}"
        #         f"</div>", unsafe_allow_html=True
        #     )
        # if 'spl_result' in st.session_state:
        #     st.subheader("📜 생성된 SPL 룰 및 검증 결과")

        #     # 🔹 불필요한 </div> 문자열 제거
        #     clean_result = st.session_state['spl_result'].replace("</div>", "").strip()

        #     st.markdown(
        #         f"""
        #         <div style='max-height:400px; overflow-y:auto;
        #                     background-color:#f8f9fa; padding:15px;
        #                     border-radius:5px; font-size:15px;
        #                     white-space: pre-wrap; word-wrap: break-word;'>
        #         {clean_result}
                
        #         """,
        #         unsafe_allow_html=True
        #     )
        import re
        if 'spl_result' in st.session_state:
            st.subheader("📜 생성된 SPL 룰 및 검증 결과")

            clean_result = st.session_state['spl_result']
            # 🔹 주석 메타데이터 지우기
            clean_result = re.sub(r"<!--.*?-->", "", clean_result, flags=re.DOTALL).strip()

            st.markdown(
                f"""
                <div style='max-height:400px; overflow-y:auto;
                            background-color:#f8f9fa; padding:15px;
                            border-radius:5px; font-size:15px;'>
                """,
                unsafe_allow_html=True
            )
            st.markdown(clean_result)  # 이제 깔끔하게 출력
            st.markdown("</div>", unsafe_allow_html=True)

            
    
    with tab2:
        st.header("📋 샘플 시나리오 선택")
        
        samples = scenario_manager.get_sample_scenarios()
        
        cols = st.columns(2)
        for idx, (key, scenario) in enumerate(samples.items()):
            with cols[idx % 2]:
                with st.container():
                    st.markdown(f"### {scenario['title']}")
                    st.write(scenario['description'])
                    
                    # 로그 타입들 표시
                    log_types = " | ".join([log['name'] for log in scenario['log_types']])
                    st.markdown(f"**생성 로그:** {log_types}")
                    
                    if st.button(f"선택", key=f"sample_{key}", use_container_width=True):
                        st.session_state['processed_scenario'] = scenario
                        st.success(f"✅ {scenario['title']} 선택됨!")
                        st.rerun()
    
    with tab3:
        st.header("📥 생성된 로그 파일")
        
        if 'generated_logs' in st.session_state:
            display_generated_logs(st.session_state['generated_logs'], download_manager)
        else:
            st.info("아직 생성된 로그가 없습니다. 먼저 시나리오를 설정하고 로그를 생성해주세요.")

def display_processed_scenario(scenario):
    """처리된 시나리오 표시"""
    st.subheader("🔍 분석된 시나리오")
    
    with st.container():
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 📅 공격 타임라인")
            for i, step in enumerate(scenario['timeline'], 1):
                st.markdown(f"{i}. {step}")
        
        with col2:
            st.markdown("#### 📊 생성될 로그 종류")
            for log_type in scenario['log_types']:
                st.markdown(f"**{log_type['name']}**: {log_type['description']}")

def generate_logs(scenario, log_generator, log_count):
    """로그 생성 함수"""
    with st.spinner("로그 파일들을 생성하는 중..."):
        try:
            # 진행률 표시
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            generated_logs = {}
            total_logs = len(scenario['log_types'])
            
            for idx, log_type in enumerate(scenario['log_types']):
                status_text.text(f"생성 중: {log_type['name']} ({idx + 1}/{total_logs})")
                
                log_content = log_generator.generate_log_content(
                    log_type, log_count, scenario
                )
                
                generated_logs[log_type['type']] = {
                    'name': log_type['name'],
                    'content': log_content,
                    'filename': f"{log_type['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                }
                
                # 진행률 업데이트
                progress = (idx + 1) / total_logs
                progress_bar.progress(progress)
            
            st.session_state['generated_logs'] = generated_logs
            status_text.text("✅ 모든 로그 생성 완료!")
            st.success(f"🎉 {total_logs}개의 로그 파일이 생성되었습니다!")
            
        except Exception as e:
            st.error(f"❌ 로그 생성 실패: {str(e)}")

def display_generated_logs(generated_logs, download_manager):
    """생성된 로그 파일 표시 및 다운로드"""
    st.markdown(f"**총 {len(generated_logs)}개의 로그 파일이 생성되었습니다.**")
    
    # 전체 다운로드 버튼
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("📦 전체 ZIP 다운로드", type="primary", use_container_width=True):
            zip_data = download_manager.create_zip_archive(generated_logs)
            st.download_button(
                label="🗂️ logs_archive.zip 다운로드",
                data=zip_data,
                file_name=f"logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
                mime="application/zip",
                use_container_width=True
            )
    
    st.divider()
    
    # 개별 파일 다운로드
    cols = st.columns(2)
    for idx, (log_type, log_data) in enumerate(generated_logs.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"### {log_data['name']}")
                
                lines = log_data['content'].split('\n')
                st.write(f"📄 **라인 수:** {len(lines):,}개")
                st.write(f"📏 **파일 크기:** {len(log_data['content'].encode('utf-8')):,} bytes")
                
                # 미리보기
                with st.expander("👀 미리보기"):
                    preview_lines = lines[:10]
                    st.code('\n'.join(preview_lines), language='text')
                    if len(lines) > 10:
                        st.write(f"... ({len(lines) - 10}개 라인 더)")
                
                # 다운로드 버튼
                st.download_button(
                    label=f"📥 {log_data['filename']}",
                    data=log_data['content'],
                    file_name=log_data['filename'],
                    mime="text/plain",
                    use_container_width=True
                )

if __name__ == "__main__":
    main()