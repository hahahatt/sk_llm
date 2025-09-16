#!/usr/bin/env python3
"""
시나리오 기반 다중 로그 생성기 - 메인 애플리케이션 (학습 기능 통합)
"""

import streamlit as st
import os
from datetime import datetime
from dotenv import load_dotenv

# --- 기존 모듈 ---
from src.nlp_processor import NLPProcessor
from src.scenario_manager import ScenarioManager
from src.log_generator import LogGenerator
from src.download_manager import DownloadManager
from src.query_optimizer_service import QueryOptimizerService
# --- 기능 추가를 위해 새로 임포트 ---
from src.case_library_manager import CaseLibraryManager
from src.progress_manager import ProgressManager

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from back.explain import explain_spl_markdown_backend

def main():
    st.set_page_config(
        page_title="SPLearn",
        page_icon="🚀",
        layout="wide"
    )
    
    # --- 사이드바 UI (사용자 이름 입력 추가) ---
    with st.sidebar:
        st.header("👤 사용자")
        user_id = st.text_input("사용자 이름을 입력하세요", placeholder="학습 기록을 위해 이름 입력")

        st.divider()
        st.header("🔑 설정")
        load_dotenv()
        api_key = os.getenv('OPENAI_API_KEY', '')
        
        if api_key:
            st.success("✅ API 키 설정됨")
        else:
            st.warning("⚠️ .env 파일에 API 키를 설정해주세요.")
        
        st.divider()
        st.header("📊 생성 설정")
        log_count = st.number_input("로그 개수 (파일당)", min_value=100, max_value=10000, value=1000, step=100)
    
    # --- 메인 헤더 (기존과 동일) ---
    st.title("🚀 SPLearn")
    st.markdown("**SPLunk의 학습을 돕습니다.**")
    
    # --- 필수 입력값 검증 ---
    if not api_key:
        st.error("먼저 .env 파일에 OpenAI API 키를 설정해주세요.")
        return
    if not user_id:
        st.info("사이드바에 사용자 이름을 입력하면 학습 기능이 활성화됩니다.")
        return
    
    # --- 사용자 변경 감지 및 세션 초기화 로직 ---
    if 'current_user_id' not in st.session_state:
        st.session_state['current_user_id'] = user_id

    if st.session_state['current_user_id'] != user_id:
        # 사용자가 변경되었으므로, 이전 사용자의 작업 내용을 초기화합니다.
        keys_to_clear = ['processed_scenario', 'generated_logs', 'optimized_spl']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        # 현재 사용자를 업데이트하고 화면을 새로고침하여 초기화된 상태를 즉시 반영합니다.
        st.session_state['current_user_id'] = user_id
        st.rerun()
    
    # --- 컴포넌트 초기화 (사용자별 관리자 추가) ---
    progress_manager = ProgressManager()
    case_library_manager = CaseLibraryManager(user_id=user_id)
    nlp_processor = NLPProcessor(api_key)
    scenario_manager = ScenarioManager()
    log_generator = LogGenerator()
    download_manager = DownloadManager()
    query_processor = QueryOptimizerService(api_key, model=os.getenv("OPENAI_MODEL", "gpt-4.1"))
    
    # --- 탭 구성 (순서 변경) ---
    tab_list = [
        "📝 시나리오 입력", "📥 생성된 로그", "🔍 Splunk Query 생성",
        "📊 학습 대시보드", "📋 샘플 시나리오", "🗂️ 케이스 라이브러리"
    ]
    tab_input, tab_logs, tab_query, tab_dashboard, tab_samples, tab_library = st.tabs(tab_list)

    # --- 학습 대시보드 탭 구현 ---
    with tab_dashboard:
        st.header(f"📊 {user_id}님의 학습 대시보드")
        all_scenarios = list(scenario_manager.get_sample_scenarios().values()) + case_library_manager.load_cases()
        stats = progress_manager.get_dashboard_stats(user_id, all_scenarios)

        col1, col2, col3 = st.columns(3)
        col1.metric("총 시나리오", f"{stats['total_count']}개")
        col2.metric("완료", f"{stats['completed_count']}개")
        col3.metric("달성률", f"{stats['completion_rate']:.1%}")
        st.progress(stats['completion_rate'])
        
        st.subheader("난이도별 진행도")
        stats_by_difficulty = stats['stats_by_difficulty']
        cols = st.columns(len(stats_by_difficulty))
        for i, (diff, data) in enumerate(stats_by_difficulty.items()):
            with cols[i]:
                st.markdown(f"**{diff}**")
                rate = data['completed'] / data['total'] if data['total'] > 0 else 0
                st.progress(rate, text=f"{data['completed']} / {data['total']}개")

    # --- 시나리오 입력 탭 (기존과 동일) ---
    with tab_input:
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
                    # generate_logs 함수 호출에 user_id와 progress_manager 추가
                    generate_logs(st.session_state['processed_scenario'], log_generator, log_count, user_id, progress_manager)
                else:
                    st.warning("먼저 시나리오를 분석해주세요.")
        
        with col3:
            if st.button("🔎 SPL 룰 검증", type="secondary", use_container_width=True):
                if "optimized_spl" not in st.session_state:
                    st.warning("먼저 Splunk 쿼리를 생성하세요. (탭4에서 '🧠 쿼리 생성/최적화' 버튼을 눌러주세요)")
                else:
                    with st.spinner("AI가 SPL 룰을 검증하는 중..."):
                        try:
                            spl_query = st.session_state["optimized_spl"]
                            spl_result = explain_spl_markdown_backend(spl_query)
                            st.session_state['spl_result'] = spl_result
                            st.success("✅ SPL 룰 검증 완료!")
                        except Exception as e:
                            st.error(f"❌ SPL 룰 검증 실패: {str(e)}")
        
        if 'processed_scenario' in st.session_state:
            display_processed_scenario(st.session_state['processed_scenario'])
    
        import re
        if 'spl_result' in st.session_state:
            st.subheader("📜 생성된 SPL 룰 및 검증 결과")

            clean_result = st.session_state['spl_result']
            clean_result = re.sub(r"<!--.*?-->", "", clean_result, flags=re.DOTALL).strip()

            st.markdown(
                f"""
                <div style='max-height:400px; overflow-y:auto;
                            background-color:#f8f9fa; padding:15px;
                            border-radius:5px; font-size:15px;'>
                """,
                unsafe_allow_html=True
            )
            st.markdown(clean_result)
            st.markdown("</div>", unsafe_allow_html=True)

    # --- 샘플 시나리오 탭 (st.rerun() 추가하여 즉시 반응하도록 수정) ---
    with tab_samples:
        st.header("📋 샘플 시나리오 선택")
        samples = scenario_manager.get_sample_scenarios()
        
        scenarios_by_difficulty = {"초급": [], "중급": [], "고급": []}
        for scenario in samples.values():
            scenarios_by_difficulty[scenario.get("difficulty", "중급")].append(scenario)

        for difficulty, scenarios in scenarios_by_difficulty.items():
            if scenarios:
                with st.expander(f"**{difficulty} 시나리오 ({len(scenarios)}개)**", expanded=(difficulty=="초급")):
                    for scenario in scenarios:
                        if st.button(f"{scenario['title']}", key=f"sample_{scenario['id']}", use_container_width=True):
                            st.session_state['processed_scenario'] = scenario
                            st.rerun()

    # --- 케이스 라이브러리 탭 (st.rerun() 추가하여 즉시 반응하도록 수정) ---
    with tab_library:
        st.header("🗂️ 케이스 라이브러리")
        cases = case_library_manager.load_cases()
        if not cases:
            st.info("저장된 케이스가 없습니다. '생성된 로그' 탭에서 시나리오를 저장해보세요.")
        else:
            for case in cases:
                if st.button(f"{case.get('title')} (난이도: {case.get('difficulty', '미지정')})", key=f"library_{case.get('id')}", use_container_width=True):
                    st.session_state['processed_scenario'] = case
                    st.rerun()

    # --- 생성된 로그 탭 (라이브러리 저장 버튼 추가) ---
    with tab_logs:
        st.header("📥 생성된 로그 파일")
        if 'generated_logs' in st.session_state:
            if st.button("🗂️ 이 시나리오를 케이스 라이브러리에 저장", use_container_width=True):
                if case_library_manager.add_case(st.session_state.get('processed_scenario')):
                    st.success("✅ 케이스가 라이브러리에 성공적으로 저장되었습니다!")
                    st.rerun() 
                else:
                    st.warning("⚠️ 이미 라이브러리에 존재하는 케이스입니다.")
            display_generated_logs(st.session_state['generated_logs'], download_manager)
        else:
            st.info("아직 생성된 로그가 없습니다. 먼저 시나리오를 설정하고 로그를 생성해주세요.")

    # --- Splunk Query 생성 탭 (기존과 동일) ---
    with tab_query:
        st.header("📥 Splunk Query 생성")
        st.markdown("---")
        st.subheader("🔎 LLM 기반 Splunk 쿼리 생성")
        def _flatten_scenario_text(scn):
            if isinstance(scn, dict):
                parts = []
                if scn.get("title"): parts.append(str(scn["title"]))
                if scn.get("description"): parts.append(str(scn["description"]))
                if scn.get("timeline"): parts.append("\n".join(map(str, scn["timeline"])))
                return "\n".join(parts).strip()
            return (str(scn) if scn is not None else "").strip()

        if st.button("🧠 쿼리 생성/최적화", use_container_width=True):
            processed_scn  = st.session_state.get("processed_scenario")
            generated_logs = st.session_state.get("generated_logs")
            if not processed_scn:
                st.warning("시나리오가 없습니다. 탭 1에서 먼저 분석을 실행하세요.")
            else:
                scenario_text = _flatten_scenario_text(processed_scn)
                try:
                    res = query_processor.make_spl(scenario_text=scenario_text, generated_logs=generated_logs)
                    spl = (res.get("query") or "").strip()
                    if not spl: st.error("LLM이 빈 쿼리를 반환했습니다.")
                    else:
                        st.session_state["optimized_spl"] = spl
                        st.success("✅ 최적화된 쿼리를 생성했습니다.")
                except Exception as e:
                    st.error(f"쿼리 생성 실패: {e}")
        
        if "optimized_spl" in st.session_state:
            spl = st.session_state["optimized_spl"]
            st.code(spl, language="spl")
            st.download_button("optimized.spl 다운로드", data=spl + "\n", file_name="optimized.spl", mime="text/plain", use_container_width=True)
        else:
            st.info("왼쪽 버튼으로 쿼리를 생성하면 여기 표시됩니다.")

# --- 헬퍼 함수들 (generate_logs 함수 시그니처 변경) ---

def display_processed_scenario(scenario):
    st.subheader("🔍 분석된 시나리오")
    with st.container():
        col1, col2 = st.columns([1, 1])
        with col1:
            st.markdown("#### 📅 공격 타임라인")
            for i, step in enumerate(scenario['timeline'], 1): st.markdown(f"{i}. {step}")
        with col2:
            st.markdown("#### 📊 생성될 로그 종류")
            for log_type in scenario['log_types']: st.markdown(f"**{log_type['name']}**: {log_type['description']}")

def generate_logs(scenario, log_generator, log_count, user_id, progress_manager):
    with st.spinner("로그 파일들을 생성하는 중..."):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            generated_logs = {}
            total_logs = len(scenario['log_types'])
            for idx, log_type in enumerate(scenario['log_types']):
                status_text.text(f"생성 중: {log_type['name']} ({idx + 1}/{total_logs})")
                log_content = log_generator.generate_log_content(log_type, log_count, scenario)
                generated_logs[log_type['type']] = {
                    'name': log_type['name'], 'content': log_content,
                    'filename': f"{log_type['type']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                }
                progress = (idx + 1) / total_logs
                progress_bar.progress(progress)
            
            st.session_state['generated_logs'] = generated_logs
            status_text.text("✅ 모든 로그 생성 완료!")
            
            # 진행도 기록 및 새로고침
            scenario_id = scenario.get('id')
            if scenario_id:
                progress_manager.mark_scenario_completed(user_id, scenario_id)
                st.success(f"🎉 로그 생성 완료! 학습 진행도에 기록되었습니다.")
                st.rerun()
            else:
                st.success(f"🎉 {total_logs}개의 로그 파일이 생성되었습니다!")
        except Exception as e:
            st.error(f"❌ 로그 생성 실패: {str(e)}")

def display_generated_logs(generated_logs, download_manager):
    st.markdown(f"**총 {len(generated_logs)}개의 로그 파일이 생성되었습니다.**")
    col1, col2 = st.columns([1, 3])
    with col1:
        zip_data = download_manager.create_zip_archive(generated_logs)
        st.download_button(
            label="📦 전체 ZIP 다운로드", data=zip_data,
            file_name=f"logs_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip",
            mime="application/zip", use_container_width=True, type="primary"
        )
    st.divider()
    cols = st.columns(2)
    for idx, (log_type, log_data) in enumerate(generated_logs.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"### {log_data['name']}")
                lines = log_data['content'].split('\n')
                st.write(f"📄 **라인 수:** {len(lines):,}개")
                st.write(f"📏 **파일 크기:** {len(log_data['content'].encode('utf-8')):,} bytes")
                with st.expander("👀 미리보기"):
                    preview_lines = lines[:10]
                    st.code('\n'.join(preview_lines), language='text')
                    if len(lines) > 10: st.write(f"... ({len(lines) - 10}개 라인 더)")
                st.download_button(
                    label=f"📥 {log_data['filename']}", data=log_data['content'],
                    file_name=log_data['filename'], mime="text/plain", use_container_width=True
                )

if __name__ == "__main__":
    main()

